from app.schemas.report import RetrievedExample
from app.services.extraction.normalizer import normalize_skill
from app.services.rag.embeddings import EmbeddingService, cosine_similarity_score
from app.services.rag.knowledge_base import KnowledgeBase, KnowledgeBaseExample

SKILL_MATCH_BOOST = 15.0


class ResumeExampleRetriever:
    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self._knowledge_base = knowledge_base or KnowledgeBase()
        self._embedding_service = embedding_service or EmbeddingService()

    def retrieve(
        self,
        resume_text: str,
        vacancy_text: str = "",
        missing_skills: list[str] | None = None,
        limit: int = 5,
    ) -> list[RetrievedExample]:
        examples = list(self._knowledge_base.examples)
        if limit <= 0 or not examples:
            return []

        query = _query_text(resume_text, vacancy_text, missing_skills or [])
        if not query:
            return []

        query_vector = self._embedding_service.embed([query])[0]
        example_vectors = self._embedding_service.embed(
            [example.searchable_text() for example in examples]
        )
        missing_skill_set = {normalize_skill(skill) for skill in missing_skills or []}

        scored = [
            (
                _score_example(query_vector, vector, example, missing_skill_set),
                example,
            )
            for example, vector in zip(examples, example_vectors, strict=True)
        ]
        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].skill.lower(),
                item[1].category.lower(),
                item[1].example_bullet.lower(),
            )
        )

        return [
            RetrievedExample(
                skill=example.skill,
                category=example.category,
                example_bullet=example.example_bullet,
                relevance_score=score,
            )
            for score, example in scored[:limit]
        ]


def _query_text(resume_text: str, vacancy_text: str, missing_skills: list[str]) -> str:
    parts = [
        resume_text.strip(),
        vacancy_text.strip(),
        " ".join(sorted({normalize_skill(skill) for skill in missing_skills})),
    ]
    return "\n".join(part for part in parts if part)


def _score_example(
    query_vector: list[float],
    example_vector: list[float],
    example: KnowledgeBaseExample,
    missing_skills: set[str],
) -> float:
    score = cosine_similarity_score(query_vector, example_vector)
    if normalize_skill(example.skill) in missing_skills:
        score = min(100.0, score + SKILL_MATCH_BOOST)
    return round(score, 2)
