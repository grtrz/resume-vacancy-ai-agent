import json
import re
from pathlib import Path

from app.schemas.report import RetrievedExample
from app.services.generation.recommendation_engine import (
    RecommendationEngine,
    build_recommendations,
)
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.knowledge_base import KnowledgeBase
from app.services.rag.retriever import ResumeExampleRetriever


class FakeEmbeddingModel:
    _concepts = (
        {"api", "backend", "fastapi", "python", "service"},
        {"database", "postgresql", "sql"},
        {"frontend", "react", "typescript", "ui"},
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


def test_knowledge_base_loads_json_examples(tmp_path: Path) -> None:
    knowledge_base_dir = _write_knowledge_base(tmp_path)

    knowledge_base = KnowledgeBase(knowledge_base_dir)

    assert [example.skill for example in knowledge_base.examples] == ["postgresql", "react"]
    assert knowledge_base.examples[0].example_bullet.startswith("Optimized PostgreSQL")


def test_retriever_returns_relevant_top_k_examples(tmp_path: Path) -> None:
    retriever = ResumeExampleRetriever(
        knowledge_base=KnowledgeBase(_write_knowledge_base(tmp_path)),
        embedding_service=EmbeddingService(model=FakeEmbeddingModel()),
    )

    examples = retriever.retrieve(
        resume_text="Built Python FastAPI backend APIs.",
        vacancy_text="Need PostgreSQL database work for backend services.",
        missing_skills=["postgresql"],
        limit=1,
    )

    assert len(examples) == 1
    assert examples[0].skill == "postgresql"
    assert examples[0].relevance_score > 50.0


def test_recommendation_engine_grounds_suggestions_in_retrieved_examples(tmp_path: Path) -> None:
    retriever = ResumeExampleRetriever(
        knowledge_base=KnowledgeBase(_write_knowledge_base(tmp_path)),
        embedding_service=EmbeddingService(model=FakeEmbeddingModel()),
    )
    engine = RecommendationEngine(retriever)

    recommendations, retrieved_examples = engine.recommend(
        resume_text="Built Python FastAPI backend APIs.",
        vacancy_text="Need PostgreSQL database work for backend services.",
        missing_skills=["postgresql"],
        limit=2,
    )

    assert retrieved_examples[0].skill == "postgresql"
    assert len(recommendations) == 1
    assert recommendations[0].skill == "postgresql"
    assert recommendations[0].category == "missing_skill_gap"
    assert "missing skill 'postgresql'" in recommendations[0].suggestion
    assert recommendations[0].example_bullet == retrieved_examples[0].example_bullet


def test_recommendation_engine_adds_strengthening_suggestions_with_missing_skills(
    tmp_path: Path,
) -> None:
    retriever = ResumeExampleRetriever(
        knowledge_base=KnowledgeBase(_write_knowledge_base(tmp_path)),
        embedding_service=EmbeddingService(model=FakeEmbeddingModel()),
    )
    engine = RecommendationEngine(retriever)

    recommendations, _ = engine.recommend(
        resume_text="Built Python FastAPI backend APIs.",
        vacancy_text="Need Python and PostgreSQL database work for backend services.",
        missing_skills=["postgresql"],
        matched_skills=["python"],
        limit=3,
    )

    by_category = {recommendation.category: recommendation for recommendation in recommendations}
    assert "missing_skill_gap" in by_category
    assert "strengthen_existing_experience" in by_category
    assert by_category["missing_skill_gap"].skill == "postgresql"
    assert by_category["strengthen_existing_experience"].skill == "python"


def test_recommendation_engine_strengthens_matches_when_no_skills_are_missing(
    tmp_path: Path,
) -> None:
    retriever = ResumeExampleRetriever(
        knowledge_base=KnowledgeBase(_write_knowledge_base(tmp_path)),
        embedding_service=EmbeddingService(model=FakeEmbeddingModel()),
    )
    engine = RecommendationEngine(retriever)

    recommendations, retrieved_examples = engine.recommend(
        resume_text="Built PostgreSQL database services.",
        vacancy_text="Need PostgreSQL database optimization.",
        missing_skills=[],
        matched_skills=["postgresql"],
        limit=2,
    )

    assert retrieved_examples
    assert recommendations
    assert recommendations[0].skill == "postgresql"
    assert recommendations[0].category == "strengthen_existing_experience"
    assert "measurable" in recommendations[0].suggestion


def test_recommendations_do_not_include_hallucinated_skills() -> None:
    retrieved_examples = [
        RetrievedExample(
            skill="react",
            category="frontend",
            example_bullet="Built React UI components for data entry workflows.",
            relevance_score=100.0,
        )
    ]

    result = build_recommendations(
        missing_skills=["postgresql"],
        retrieved_examples=retrieved_examples,
        matched_skills=["python"],
    )

    assert {recommendation.skill for recommendation in result} <= {"postgresql", "python"}


def _write_knowledge_base(tmp_path: Path) -> Path:
    knowledge_base_dir = tmp_path / "knowledge_base"
    knowledge_base_dir.mkdir()
    (knowledge_base_dir / "examples.json").write_text(
        json.dumps(
            [
                {
                    "skill": "postgresql",
                    "category": "database",
                    "example_bullet": ("Optimized PostgreSQL indexes for reporting workloads."),
                },
                {
                    "skill": "react",
                    "category": "frontend",
                    "example_bullet": "Built React UI components for data entry workflows.",
                },
            ]
        ),
        encoding="utf-8",
    )
    return knowledge_base_dir
