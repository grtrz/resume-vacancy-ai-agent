from app.services.rag.embeddings import EmbeddingService


class SemanticMatcher:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self._embedding_service = embedding_service or EmbeddingService()

    def compare(self, left: str, right: str) -> float:
        return self._embedding_service.similarity(left, right)
