import math
from functools import cached_property, lru_cache
from typing import Any, Protocol

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingModel(Protocol):
    def encode(
        self,
        sentences: list[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> Any: ...


@lru_cache(maxsize=2)
def load_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> EmbeddingModel:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class EmbeddingService:
    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        model: EmbeddingModel | None = None,
    ) -> None:
        self._model_name = model_name
        self._model = model

    @cached_property
    def model(self) -> EmbeddingModel:
        if self._model is not None:
            return self._model
        return load_embedding_model(self._model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return [_to_float_vector(vector) for vector in vectors]

    def similarity(self, left: str, right: str) -> float:
        if not left.strip() or not right.strip():
            return 0.0

        left_vector, right_vector = self.embed([left, right])
        return cosine_similarity_score(left_vector, right_vector)


def cosine_similarity_score(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    similarity = sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=True)
    ) / (left_norm * right_norm)
    return round(max(0.0, min(1.0, similarity)) * 100, 2)


def _to_float_vector(vector: Any) -> list[float]:
    if hasattr(vector, "tolist"):
        vector = vector.tolist()
    return [float(value) for value in vector]
