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
        limit: int = 5,
    ) -> tuple[list[RecommendationSuggestion], list[RetrievedExample]]:
        if not missing_skills:
            return [], []

        retrieved_examples = self._retriever.retrieve(
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            missing_skills=missing_skills,
            limit=limit,
        )
        recommendations = build_recommendations(missing_skills, retrieved_examples)
        return recommendations, retrieved_examples


def build_recommendations(
    missing_skills: list[str],
    retrieved_examples: Iterable[RetrievedExample],
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
                category=example.category,
                suggestion=(
                    f"Address missing skill '{skill}' only if it reflects real experience. "
                    f"Use the retrieved {example.category} example as structure."
                ),
                example_bullet=example.example_bullet,
            )
        )
    return recommendations
