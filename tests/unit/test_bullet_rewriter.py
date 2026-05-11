from app.schemas.extraction import VacancyRequirements
from app.schemas.generation import BulletRewriteInput
from app.schemas.report import RetrievedExample
from app.services.generation.bullet_rewriter import BulletRewriter
from app.services.generation.llm_provider import DeterministicMockLLMProvider


def test_bullet_rewriter_uses_mock_provider_and_validates_structured_output() -> None:
    provider = DeterministicMockLLMProvider(
        {
            "suggestions": [
                {
                    "original_bullet": "Built backend APIs with Python.",
                    "rewritten_bullet": (
                        "Built backend APIs with Python and documented PostgreSQL work."
                    ),
                    "referenced_skills": ["python", "postgresql", "kubernetes"],
                    "retrieved_example_bullets": [
                        "Optimized PostgreSQL indexes for reporting workloads.",
                        "Invented example that was not retrieved.",
                    ],
                    "is_conditional": False,
                    "grounding": "Based on resume and retrieved PostgreSQL example.",
                }
            ]
        }
    )
    request = _request()

    result = BulletRewriter(provider=provider).rewrite(request)

    assert result.provider == "deterministic_mock"
    assert len(provider.requests) == 1
    assert len(result.suggestions) == 1
    suggestion = result.suggestions[0]
    assert suggestion.referenced_skills == ["python", "postgresql"]
    assert suggestion.retrieved_example_bullets == [
        "Optimized PostgreSQL indexes for reporting workloads."
    ]


def test_bullet_rewriter_marks_ungrounded_missing_skill_as_conditional() -> None:
    provider = DeterministicMockLLMProvider(
        {
            "suggestions": [
                {
                    "original_bullet": "Built backend APIs with Python.",
                    "rewritten_bullet": "Built backend APIs with Python and PostgreSQL.",
                    "referenced_skills": ["postgresql"],
                    "retrieved_example_bullets": [
                        "Optimized PostgreSQL indexes for reporting workloads."
                    ],
                    "is_conditional": False,
                    "grounding": "Uses retrieved PostgreSQL example.",
                }
            ]
        }
    )

    result = BulletRewriter(provider=provider).rewrite(_request())

    assert result.suggestions[0].is_conditional is True
    assert result.suggestions[0].rewritten_bullet.startswith("Conditional draft:")
    assert result.suggestions[0].grounding.startswith("Conditional:")


def test_bullet_rewriter_keeps_grounded_suggestion_non_conditional() -> None:
    provider = DeterministicMockLLMProvider(
        {
            "suggestions": [
                {
                    "original_bullet": "Built backend APIs with Python.",
                    "rewritten_bullet": "Built backend APIs with Python for service workflows.",
                    "referenced_skills": ["python"],
                    "retrieved_example_bullets": [],
                    "is_conditional": False,
                    "grounding": "Python appears in the original resume text.",
                }
            ]
        }
    )

    result = BulletRewriter(provider=provider).rewrite(_request())

    assert result.suggestions[0].is_conditional is False


def test_bullet_rewriter_rule_based_fallback_uses_retrieved_examples() -> None:
    result = BulletRewriter(use_configured_provider=False).rewrite(_request())

    assert result.provider == "deterministic_rule_based"
    assert len(result.suggestions) == 2
    postgresql = next(
        suggestion
        for suggestion in result.suggestions
        if suggestion.referenced_skills == ["postgresql"]
    )
    assert postgresql.is_conditional is True
    assert postgresql.retrieved_example_bullets == [
        "Optimized PostgreSQL indexes for reporting workloads."
    ]


def _request() -> BulletRewriteInput:
    return BulletRewriteInput(
        original_resume_text="Experience\n- Built backend APIs with Python.",
        vacancy_requirements=VacancyRequirements(
            required_skills=["python", "postgresql"],
            responsibilities=["Build backend APIs backed by SQL databases."],
        ),
        missing_skills=["python", "postgresql"],
        retrieved_examples=[
            RetrievedExample(
                skill="postgresql",
                category="database",
                example_bullet="Optimized PostgreSQL indexes for reporting workloads.",
                relevance_score=95.0,
            ),
            RetrievedExample(
                skill="python",
                category="backend",
                example_bullet="Built Python services for validation workflows.",
                relevance_score=90.0,
            ),
        ],
    )
