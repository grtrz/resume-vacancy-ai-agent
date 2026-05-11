from collections.abc import Iterable
from typing import Protocol

from app.schemas.extraction import ExperienceRange, ExtractedProfile, VacancyRequirements
from app.schemas.report import (
    GapItem,
    MatchScoreBreakdown,
    RecommendationSuggestion,
    ResumeVacancyReport,
    RetrievedExample,
)
from app.schemas.resume import ResumeProfile
from app.schemas.vacancy import VacancyProfile
from app.services.generation.recommendation_engine import RecommendationEngine
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


class SemanticComparator(Protocol):
    def compare(self, left: str, right: str) -> float: ...


class RecommendationGenerator(Protocol):
    def recommend(
        self,
        resume_text: str,
        vacancy_text: str,
        missing_skills: list[str],
        limit: int = 5,
    ) -> tuple[list[RecommendationSuggestion], list[RetrievedExample]]: ...


class MatchingReportBuilder:
    def __init__(
        self,
        semantic_matcher: SemanticComparator | None = None,
        recommendation_engine: RecommendationGenerator | None = None,
    ) -> None:
        self._semantic_matcher = semantic_matcher or SemanticMatcher()
        self._recommendation_engine = recommendation_engine or RecommendationEngine()

    def build(
        self,
        resume: ResumeProfile | ExtractedProfile,
        vacancy: VacancyProfile | VacancyRequirements,
    ) -> ResumeVacancyReport:
        resume_profile = _resume_extracted_profile(resume)
        vacancy_requirements = _vacancy_requirements(vacancy)

        resume_skills = _resume_skills(resume_profile)
        required_skills = vacancy_requirements.required_skills
        preferred_skills = vacancy_requirements.preferred_skills
        vacancy_skills = [*required_skills, *preferred_skills]
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
        resume_semantic_text = _resume_semantic_text(resume, resume_profile)
        vacancy_semantic_text = _vacancy_semantic_text(vacancy, vacancy_requirements)
        semantic_similarity = self._semantic_matcher.compare(
            resume_semantic_text,
            vacancy_semantic_text,
        )
        match_score = weighted_final_score(
            skills_overlap,
            experience_match,
            keyword_relevance,
            coverage_bonus,
            semantic_similarity,
        )

        missing = missing_skills(resume_skills, required_skills)
        recommendations, retrieved_examples = self._recommendation_engine.recommend(
            resume_text=resume_semantic_text,
            vacancy_text=vacancy_semantic_text,
            missing_skills=missing,
        )

        return ResumeVacancyReport(
            resume_id=resume.id if isinstance(resume, ResumeProfile) else None,
            vacancy_id=vacancy.id if isinstance(vacancy, VacancyProfile) else None,
            match_score=match_score,
            score_breakdown=MatchScoreBreakdown(
                skills_overlap=skills_overlap,
                experience_match=experience_match,
                keyword_relevance=keyword_relevance,
                coverage_bonus=coverage_bonus,
                semantic_similarity=semantic_similarity,
            ),
            matched_skills=matched_skills(resume_skills, vacancy_skills),
            missing_skills=missing,
            gaps=_gap_items(missing, recommendations),
            recommendations=recommendations,
            retrieved_examples=retrieved_examples,
        )


def build_matching_report(
    resume: ResumeProfile | ExtractedProfile,
    vacancy: VacancyProfile | VacancyRequirements,
) -> ResumeVacancyReport:
    return MatchingReportBuilder().build(resume, vacancy)


def _resume_extracted_profile(resume: ResumeProfile | ExtractedProfile) -> ExtractedProfile:
    if isinstance(resume, ResumeProfile):
        return resume.extracted
    return resume


def _vacancy_requirements(vacancy: VacancyProfile | VacancyRequirements) -> VacancyRequirements:
    if isinstance(vacancy, VacancyProfile):
        return vacancy.requirements
    return vacancy


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


def _resume_semantic_text(
    resume: ResumeProfile | ExtractedProfile,
    profile: ExtractedProfile,
) -> str:
    if isinstance(resume, ResumeProfile) and resume.raw_text.strip():
        return resume.raw_text
    return "\n".join(_resume_keyword_terms(profile))


def _vacancy_semantic_text(
    vacancy: VacancyProfile | VacancyRequirements,
    requirements: VacancyRequirements,
) -> str:
    if isinstance(vacancy, VacancyProfile) and vacancy.raw_text.strip():
        return vacancy.raw_text
    return "\n".join(_vacancy_keyword_terms(requirements))


def _gap_items(
    missing: list[str],
    recommendations: list[RecommendationSuggestion],
) -> list[GapItem]:
    recommendation_by_skill = {
        recommendation.skill: recommendation.suggestion for recommendation in recommendations
    }
    return [
        GapItem(
            category="skill",
            requirement=skill,
            recommendation=recommendation_by_skill.get(skill),
        )
        for skill in missing
    ]
