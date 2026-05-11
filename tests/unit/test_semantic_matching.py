import re

from app.services.matching.scoring import semantic_similarity_score
from app.services.rag.embeddings import EmbeddingService


class FakeEmbeddingModel:
    _concepts = (
        {"api", "apis", "backend", "database", "fastapi", "postgresql", "python", "service"},
        {"campaign", "content", "marketing", "sales"},
        {"css", "frontend", "react", "typescript", "ui"},
    )

    def encode(
        self,
        sentences: list[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> list[list[float]]:
        return [self._vectorize(sentence) for sentence in sentences]

    def _vectorize(self, sentence: str) -> list[float]:
        tokens = set(re.findall(r"[a-z0-9+#]+", sentence.lower()))
        return [float(len(tokens & concept)) for concept in self._concepts]


def test_semantically_similar_texts_score_higher() -> None:
    service = EmbeddingService(model=FakeEmbeddingModel())

    similar_score = semantic_similarity_score(
        "Built Python backend APIs with FastAPI and PostgreSQL.",
        "Hiring backend engineer for Python API services and database work.",
        service,
    )
    unrelated_score = semantic_similarity_score(
        "Built Python backend APIs with FastAPI and PostgreSQL.",
        "Created marketing campaigns, sales content, and brand messaging.",
        service,
    )

    assert similar_score > unrelated_score
    assert similar_score > 50.0


def test_unrelated_texts_score_lower() -> None:
    service = EmbeddingService(model=FakeEmbeddingModel())

    score = semantic_similarity_score(
        "Built Python backend APIs with FastAPI and PostgreSQL.",
        "Created marketing campaigns, sales content, and brand messaging.",
        service,
    )

    assert 0.0 <= score <= 100.0
    assert score < 50.0
