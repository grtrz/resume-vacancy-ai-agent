from app.schemas.report import ResumeVacancyReport
from app.services.evaluation.matching_evaluator import (
    EvaluationMetrics,
    EvaluationPair,
    EvaluationResult,
    compute_metrics,
    evaluate_pairs,
    load_evaluation_pairs,
)


def test_load_evaluation_pairs_reads_dataset() -> None:
    pairs = load_evaluation_pairs()

    assert len(pairs) == 5
    assert {pair.id for pair in pairs} == {
        "experience_mismatch",
        "missing_skills",
        "semantic_low_exact_overlap",
        "strong_match",
        "weak_match",
    }
    assert all(pair.description for pair in pairs)


def test_compute_metrics_aggregates_expected_skill_quality() -> None:
    pair_a = _pair(
        expected_missing_skills=["docker", "postgresql"],
        expected_matched_skills=["python", "fastapi"],
        expected_min_score=80,
        expected_max_score=100,
    )
    pair_b = _pair(
        expected_missing_skills=["kubernetes"],
        expected_matched_skills=["python"],
        expected_min_score=60,
        expected_max_score=70,
    )
    results = [
        EvaluationResult(
            pair=pair_a,
            report=_report(
                match_score=90,
                missing_skills=["docker"],
                matched_skills=["python", "fastapi", "sql"],
            ),
        ),
        EvaluationResult(
            pair=pair_b,
            report=_report(
                match_score=50,
                missing_skills=["kubernetes"],
                matched_skills=["python"],
            ),
        ),
    ]

    metrics = compute_metrics(results)

    assert metrics == EvaluationMetrics(
        score_in_expected_range_rate=0.5,
        missing_skill_recall=0.6667,
        matched_skill_precision=0.75,
        average_match_score=70.0,
    )


def test_evaluate_pairs_uses_injected_report_runner() -> None:
    pairs = [_pair(expected_min_score=70, expected_max_score=90)]

    results = evaluate_pairs(
        pairs,
        report_runner=lambda pair: _report(
            match_score=80,
            missing_skills=pair.expected_missing_skills,
            matched_skills=pair.expected_matched_skills,
        ),
    )

    assert len(results) == 1
    assert results[0].score_in_expected_range is True


def _pair(
    expected_missing_skills: list[str] | None = None,
    expected_matched_skills: list[str] | None = None,
    expected_min_score: float = 0,
    expected_max_score: float = 100,
) -> EvaluationPair:
    return EvaluationPair(
        id="case",
        description="Synthetic evaluation pair.",
        resume_text="Skills\nPython",
        vacancy_text="Skills\nPython",
        expected_min_score=expected_min_score,
        expected_max_score=expected_max_score,
        expected_missing_skills=expected_missing_skills or [],
        expected_matched_skills=expected_matched_skills or [],
    )


def _report(
    match_score: float,
    missing_skills: list[str],
    matched_skills: list[str],
) -> ResumeVacancyReport:
    return ResumeVacancyReport(
        match_score=match_score,
        missing_skills=missing_skills,
        matched_skills=matched_skills,
    )
