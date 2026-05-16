from app.schemas.generation import BulletRewriteInput, BulletRewriteResult, BulletRewriteSuggestion
from app.schemas.report import RetrievedExample
from app.services.agents.nodes import WorkflowNodes
from app.services.agents.workflow import WORKFLOW_ORDER, run_workflow
from app.services.extraction.skill_extractor import SkillExtractor


class StaticSemanticMatcher:
    def compare(self, left: str, right: str) -> float:
        return 88.0 if left and right else 0.0


class StaticRetriever:
    def retrieve(
        self,
        resume_text: str,
        vacancy_text: str = "",
        missing_skills: list[str] | None = None,
        limit: int = 5,
    ) -> list[RetrievedExample]:
        _ = resume_text
        _ = vacancy_text
        _ = limit
        missing = set(missing_skills or [])
        if "postgresql" not in missing:
            return []
        return [
            RetrievedExample(
                skill="postgresql",
                category="database",
                example_bullet="Optimized PostgreSQL indexes for reporting workloads.",
                relevance_score=91.0,
            )
        ]


class StaticBulletRewriter:
    def rewrite(self, request: BulletRewriteInput) -> BulletRewriteResult:
        assert "postgresql" in request.missing_skills
        return BulletRewriteResult(
            provider="static",
            suggestions=[
                BulletRewriteSuggestion(
                    original_bullet=None,
                    rewritten_bullet=(
                        "Conditional draft: add PostgreSQL impact only with real evidence."
                    ),
                    referenced_skills=["postgresql"],
                    retrieved_example_bullets=[
                        "Optimized PostgreSQL indexes for reporting workloads."
                    ],
                    is_conditional=True,
                    grounding="Conditional: PostgreSQL is missing from the resume text.",
                )
            ],
        )


def test_workflow_executes_successfully_in_deterministic_order() -> None:
    state = run_workflow(
        resume_text="""
        Skills
        Python
        Experience
        4 years building backend APIs.
        """,
        vacancy_text="""
        Skills
        Python, PostgreSQL
        Experience
        At least 3 years building backend APIs.
        """,
        nodes=_nodes(),
    )

    assert state.completed_nodes == list(WORKFLOW_ORDER)
    assert set(state.workflow_timings_ms) == set(WORKFLOW_ORDER)
    assert all(duration >= 0 for duration in state.workflow_timings_ms.values())
    assert state.cleaned_resume_text.startswith("Skills")
    assert state.resume_profile is not None
    assert state.vacancy_requirements is not None
    assert state.semantic_similarity == 88.0
    assert state.missing_skills == ["postgresql"]
    assert len(state.retrieved_examples) == 1
    assert {recommendation.category for recommendation in state.recommendations} == {
        "missing_skill_gap",
        "strengthen_existing_experience",
    }
    assert state.report is not None
    assert state.report.retrieved_examples == state.retrieved_examples
    assert state.report.recommendations == state.recommendations


def test_workflow_runs_optional_bullet_rewriting_when_enabled() -> None:
    state = run_workflow(
        resume_text="Skills\nPython\nExperience\nBuilt backend APIs.",
        vacancy_text="Skills\nPython, PostgreSQL\nExperience\nAt least 3 years.",
        enable_bullet_rewriting=True,
        nodes=_nodes(),
    )

    assert state.bullet_rewrite_result is not None
    assert "optional_bullet_rewriting" in state.workflow_timings_ms
    assert state.workflow_timings_ms["optional_bullet_rewriting"] >= 0
    assert state.bullet_rewrite_result.provider == "static"
    assert state.report is not None
    assert state.report.improved_bullets == [
        "Conditional draft: add PostgreSQL impact only with real evidence."
    ]


def _nodes() -> WorkflowNodes:
    return WorkflowNodes(
        extractor=SkillExtractor(),
        semantic_matcher=StaticSemanticMatcher(),
        retriever=StaticRetriever(),
        bullet_rewriter=StaticBulletRewriter(),
    )
