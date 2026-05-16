from collections.abc import Iterable

from app.schemas.report import RecommendationSuggestion, RetrievedExample
from app.services.extraction.normalizer import normalize_skill
from app.services.rag.retriever import ResumeExampleRetriever


class RecommendationEngine:
    def __init__(self, retriever: ResumeExampleRetriever | None = None) -> None:
        self._retriever = retriever or ResumeExampleRetriever()

    def recommend(
        self,
        resume_text: str,
        vacancy_text: str,
        missing_skills: list[str],
        matched_skills: list[str] | None = None,
        limit: int = 5,
    ) -> tuple[list[RecommendationSuggestion], list[RetrievedExample]]:
        target_skills = _target_skills(missing_skills, matched_skills or [], limit)
        if not target_skills:
            return [], []

        retrieved_examples = self._retriever.retrieve(
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            missing_skills=target_skills,
            limit=limit,
        )
        recommendations = build_recommendations(
            missing_skills,
            retrieved_examples,
            matched_skills=matched_skills or [],
        )
        return recommendations, retrieved_examples


def build_recommendations(
    missing_skills: list[str],
    retrieved_examples: Iterable[RetrievedExample],
    matched_skills: list[str] | None = None,
    strengthening_limit: int = 3,
) -> list[RecommendationSuggestion]:
    examples_by_skill: dict[str, list[RetrievedExample]] = {}
    for example in retrieved_examples:
        examples_by_skill.setdefault(normalize_skill(example.skill), []).append(example)

    recommendations: list[RecommendationSuggestion] = []
    for skill in sorted({normalize_skill(skill) for skill in missing_skills}):
        examples = examples_by_skill.get(skill, [])
        if not examples:
            continue

        example = examples[0]
        recommendations.append(
            RecommendationSuggestion(
                skill=skill,
                category="missing_skill_gap",
                suggestion=(
                    f"Address missing skill '{skill}' only if it reflects real experience. "
                    f"Use the retrieved {example.category} example as structure."
                ),
                example_bullet=example.example_bullet,
            )
        )
    recommendations.extend(
        _strengthening_recommendations(
            matched_skills or [],
            examples_by_skill,
            limit=strengthening_limit,
        )
    )
    return recommendations


def _strengthening_recommendations(
    matched_skills: list[str],
    examples_by_skill: dict[str, list[RetrievedExample]],
    limit: int,
) -> list[RecommendationSuggestion]:
    recommendations: list[RecommendationSuggestion] = []
    for skill in sorted({normalize_skill(skill) for skill in matched_skills})[:limit]:
        example = _example_for_skill(skill, examples_by_skill)
        recommendations.append(
            RecommendationSuggestion(
                skill=skill,
                category="strengthen_existing_experience",
                suggestion=(
                    f"Strengthen existing {skill} experience by making it measurable, "
                    "specific to the vacancy, and grounded in work already present in the resume. "
                    "Do not add tools, outcomes, or scope that are not supported by the "
                    "original text."
                ),
                example_bullet=example.example_bullet,
            )
        )
    return recommendations


def _example_for_skill(
    skill: str,
    examples_by_skill: dict[str, list[RetrievedExample]],
) -> RetrievedExample:
    examples = examples_by_skill.get(skill, [])
    if examples:
        return examples[0]
    return RetrievedExample(
        skill=skill,
        category="strengthening",
        example_bullet=(
            f"Use an existing resume bullet that already mentions {skill}; add concrete "
            "scope, scale, reliability, latency, quality, or business impact only when supported."
        ),
        relevance_score=0.0,
    )


def _target_skills(
    missing_skills: list[str],
    matched_skills: list[str],
    limit: int,
) -> list[str]:
    normalized = [normalize_skill(skill) for skill in [*missing_skills, *matched_skills]]
    return sorted({skill for skill in normalized if skill})[:limit]
