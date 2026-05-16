from collections.abc import Iterable
from typing import Any, Protocol

from app.schemas.extraction import ExperienceRange, ExtractedProfile, VacancyRequirements
from app.schemas.generation import BulletRewriteInput, BulletRewriteResult
from app.schemas.report import (
    GapItem,
    MatchScoreBreakdown,
    ResumeVacancyReport,
    RetrievedExample,
)
from app.services.agents.state import WorkflowState
from app.services.extraction.skill_extractor import SkillExtractor
from app.services.generation.bullet_rewriter import BulletRewriter
from app.services.generation.recommendation_engine import build_recommendations
from app.services.matching.scoring import (
    coverage_bonus_score,
    experience_match_score,
    keyword_relevance_score,
    matched_skills,
    missing_skills,
    skill_overlap_score,
    weighted_final_score,
)
from app.services.matching.semantic_matcher import SemanticMatcher
from app.services.parsing.text_cleaner import clean_text
from app.services.rag.retriever import ResumeExampleRetriever


class ProfileExtractor(Protocol):
    def extract_resume(self, text: str) -> ExtractedProfile: ...

    def extract_vacancy(self, text: str) -> VacancyRequirements: ...


class SemanticComparator(Protocol):
    def compare(self, left: str, right: str) -> float: ...


class ExampleRetriever(Protocol):
    def retrieve(
        self,
        resume_text: str,
        vacancy_text: str = "",
        missing_skills: list[str] | None = None,
        limit: int = 5,
    ) -> list[RetrievedExample]: ...


class BulletRewriteService(Protocol):
    def rewrite(self, request: BulletRewriteInput) -> BulletRewriteResult: ...


class WorkflowNodes:
    def __init__(
        self,
        extractor: ProfileExtractor | None = None,
        semantic_matcher: SemanticComparator | None = None,
        retriever: ExampleRetriever | None = None,
        bullet_rewriter: BulletRewriteService | None = None,
    ) -> None:
        self._extractor = extractor or SkillExtractor()
        self._semantic_matcher = semantic_matcher or SemanticMatcher()
        self._retriever = retriever or ResumeExampleRetriever()
        self._bullet_rewriter = bullet_rewriter or BulletRewriter()

    def parse(self, state: WorkflowState | dict[str, Any]) -> dict[str, Any]:
        workflow_state = _coerce_state(state)
        workflow_state.cleaned_resume_text = clean_text(workflow_state.resume_text)
        workflow_state.cleaned_vacancy_text = clean_text(workflow_state.vacancy_text)
        return _complete(workflow_state, "parsing")

    def extract(self, state: WorkflowState | dict[str, Any]) -> dict[str, Any]:
        workflow_state = _coerce_state(state)
        workflow_state.resume_profile = self._extractor.extract_resume(
            workflow_state.cleaned_resume_text
        )
        workflow_state.vacancy_requirements = self._extractor.extract_vacancy(
            workflow_state.cleaned_vacancy_text
        )
        return _complete(workflow_state, "extraction")

    def semantic_match(self, state: WorkflowState | dict[str, Any]) -> dict[str, Any]:
        workflow_state = _coerce_state(state)
        resume_profile = _require_resume_profile(workflow_state)
        vacancy_requirements = _require_vacancy_requirements(workflow_state)

        resume_skills = _resume_skills(resume_profile)
        required_skills = vacancy_requirements.required_skills
        preferred_skills = vacancy_requirements.preferred_skills
        experience = vacancy_requirements.experience or ExperienceRange()

        skills_overlap = skill_overlap_score(resume_skills, required_skills)
        experience_match = experience_match_score(
            resume_profile.experience_years,
            experience.minimum_years,
            experience.maximum_years,
        )
        keyword_relevance = keyword_relevance_score(
            _resume_keyword_terms(resume_profile),
            _vacancy_keyword_terms(vacancy_requirements),
        )
        coverage_bonus = coverage_bonus_score(resume_skills, required_skills, preferred_skills)
        semantic_similarity = self._semantic_matcher.compare(
            workflow_state.cleaned_resume_text,
            workflow_state.cleaned_vacancy_text,
        )

        workflow_state.semantic_similarity = semantic_similarity
        workflow_state.score_breakdown = MatchScoreBreakdown(
            skills_overlap=skills_overlap,
            experience_match=experience_match,
            keyword_relevance=keyword_relevance,
            coverage_bonus=coverage_bonus,
            semantic_similarity=semantic_similarity,
        )
        workflow_state.match_score = weighted_final_score(
            skills_overlap,
            experience_match,
            keyword_relevance,
            coverage_bonus,
            semantic_similarity,
        )
        workflow_state.matched_skills = matched_skills(
            resume_skills,
            [*required_skills, *preferred_skills],
        )
        workflow_state.missing_skills = missing_skills(resume_skills, required_skills)
        return _complete(workflow_state, "semantic_matching")

    def retrieve(self, state: WorkflowState | dict[str, Any]) -> dict[str, Any]:
        workflow_state = _coerce_state(state)
        workflow_state.retrieved_examples = self._retriever.retrieve(
            resume_text=workflow_state.cleaned_resume_text,
            vacancy_text=workflow_state.cleaned_vacancy_text,
            missing_skills=workflow_state.missing_skills,
        )
        return _complete(workflow_state, "retrieval")

    def generate_recommendations(self, state: WorkflowState | dict[str, Any]) -> dict[str, Any]:
        workflow_state = _coerce_state(state)
        workflow_state.recommendations = build_recommendations(
            workflow_state.missing_skills,
            workflow_state.retrieved_examples,
            matched_skills=workflow_state.matched_skills,
        )
        workflow_state.report = _build_report(workflow_state)
        return _complete(workflow_state, "recommendation_generation")

    def rewrite_bullets(self, state: WorkflowState | dict[str, Any]) -> dict[str, Any]:
        workflow_state = _coerce_state(state)
        if not workflow_state.enable_bullet_rewriting:
            return _complete(workflow_state, "optional_bullet_rewriting")

        rewrite_result = self._bullet_rewriter.rewrite(
            BulletRewriteInput(
                original_resume_text=workflow_state.cleaned_resume_text,
                vacancy_requirements=_require_vacancy_requirements(workflow_state),
                missing_skills=workflow_state.missing_skills,
                retrieved_examples=workflow_state.retrieved_examples,
            )
        )
        workflow_state.bullet_rewrite_result = rewrite_result
        workflow_state.report = _build_report(workflow_state)
        return _complete(workflow_state, "optional_bullet_rewriting")


def build_nodes(nodes: WorkflowNodes | None = None) -> dict[str, Any]:
    resolved_nodes = nodes or WorkflowNodes()
    return {
        "parsing": resolved_nodes.parse,
        "extraction": resolved_nodes.extract,
        "semantic_matching": resolved_nodes.semantic_match,
        "retrieval": resolved_nodes.retrieve,
        "recommendation_generation": resolved_nodes.generate_recommendations,
        "optional_bullet_rewriting": resolved_nodes.rewrite_bullets,
    }


def _coerce_state(state: WorkflowState | dict[str, Any]) -> WorkflowState:
    if isinstance(state, WorkflowState):
        return state.model_copy(deep=True)
    return WorkflowState.model_validate(state)


def _complete(state: WorkflowState, node_name: str) -> dict[str, Any]:
    state.completed_nodes = [*state.completed_nodes, node_name]
    return state.model_dump(mode="python")


def _require_resume_profile(state: WorkflowState) -> ExtractedProfile:
    if state.resume_profile is None:
        msg = "Workflow extraction node must run before matching."
        raise ValueError(msg)
    return state.resume_profile


def _require_vacancy_requirements(state: WorkflowState) -> VacancyRequirements:
    if state.vacancy_requirements is None:
        msg = "Workflow extraction node must run before vacancy-dependent nodes."
        raise ValueError(msg)
    return state.vacancy_requirements


def _resume_skills(profile: ExtractedProfile) -> list[str]:
    return sorted({*profile.hard_skills, *profile.frameworks, *profile.tools})


def _resume_keyword_terms(profile: ExtractedProfile) -> Iterable[str]:
    return (
        *profile.hard_skills,
        *profile.frameworks,
        *profile.tools,
        *profile.education,
        *profile.projects,
        *profile.responsibilities,
        *profile.achievements,
        *profile.sections.values(),
    )


def _vacancy_keyword_terms(requirements: VacancyRequirements) -> Iterable[str]:
    return (
        *requirements.required_skills,
        *requirements.preferred_skills,
        *requirements.responsibilities,
        *requirements.sections.values(),
    )


def _build_report(state: WorkflowState) -> ResumeVacancyReport:
    recommendations_by_skill = {
        recommendation.skill: recommendation.suggestion
        for recommendation in state.recommendations
        if recommendation.category == "missing_skill_gap"
    }
    rewrite_suggestions = (
        state.bullet_rewrite_result.suggestions if state.bullet_rewrite_result else []
    )
    return ResumeVacancyReport(
        match_score=state.match_score,
        score_breakdown=state.score_breakdown,
        matched_skills=state.matched_skills,
        missing_skills=state.missing_skills,
        gaps=[
            GapItem(
                category="skill",
                requirement=skill,
                recommendation=recommendations_by_skill.get(skill),
            )
            for skill in state.missing_skills
        ],
        improved_bullets=[suggestion.rewritten_bullet for suggestion in rewrite_suggestions],
        recommendations=state.recommendations,
        retrieved_examples=state.retrieved_examples,
    )
