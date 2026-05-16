from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.schemas.report import RecommendationSuggestion, ResumeVacancyReport, RetrievedExample
from app.schemas.resume import ResumeProfile
from app.schemas.vacancy import VacancyProfile
from app.services.extraction.normalizer import normalize_skill
from app.services.extraction.skill_extractor import SkillExtractor
from app.services.matching.hybrid_ranker import HybridRanker
from app.services.matching.report_builder import MatchingReportBuilder
from app.services.parsing.text_cleaner import clean_text

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "evaluation" / "resume_vacancy_pairs.json"
)


@dataclass(frozen=True)
class EvaluationPair:
    id: str
    description: str
    resume_text: str
    vacancy_text: str
    expected_min_score: float
    expected_max_score: float
    expected_missing_skills: list[str]
    expected_matched_skills: list[str]


@dataclass(frozen=True)
class EvaluationResult:
    pair: EvaluationPair
    report: ResumeVacancyReport

    @property
    def score_in_expected_range(self) -> bool:
        return (
            self.pair.expected_min_score <= self.report.match_score <= self.pair.expected_max_score
        )


@dataclass(frozen=True)
class EvaluationMetrics:
    score_in_expected_range_rate: float
    missing_skill_recall: float
    matched_skill_precision: float
    average_match_score: float


class DeterministicSemanticMatcher:
    def compare(self, left: str, right: str) -> float:
        left_terms = _semantic_terms(left)
        right_terms = _semantic_terms(right)
        if not left_terms or not right_terms:
            return 0.0

        overlap = len(left_terms & right_terms) / len(left_terms | right_terms)
        return round(min(100.0, 35.0 + overlap * 90.0), 2)


class NoOpRecommendationEngine:
    def recommend(
        self,
        resume_text: str,
        vacancy_text: str,
        missing_skills: list[str],
        matched_skills: list[str] | None = None,
        limit: int = 5,
    ) -> tuple[list[RecommendationSuggestion], list[RetrievedExample]]:
        _ = resume_text
        _ = vacancy_text
        _ = missing_skills
        _ = matched_skills
        _ = limit
        return [], []


ReportRunner = Callable[[EvaluationPair], ResumeVacancyReport]


def load_evaluation_pairs(path: Path = DEFAULT_DATASET_PATH) -> list[EvaluationPair]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        msg = "Evaluation dataset must be a JSON array."
        raise ValueError(msg)
    return [EvaluationPair(**item) for item in payload]


def build_report_for_pair(
    pair: EvaluationPair,
    extractor: SkillExtractor | None = None,
    ranker: HybridRanker | None = None,
) -> ResumeVacancyReport:
    resolved_extractor = extractor or SkillExtractor()
    resolved_ranker = ranker or evaluation_ranker()
    resume_text = clean_text(pair.resume_text)
    vacancy_text = clean_text(pair.vacancy_text)
    resume = ResumeProfile(
        raw_text=resume_text,
        extracted=resolved_extractor.extract_resume(resume_text),
    )
    vacancy = VacancyProfile(
        raw_text=vacancy_text,
        requirements=resolved_extractor.extract_vacancy(vacancy_text),
    )
    return resolved_ranker.compare(resume, vacancy)


def evaluate_pairs(
    pairs: list[EvaluationPair],
    report_runner: ReportRunner = build_report_for_pair,
) -> list[EvaluationResult]:
    return [EvaluationResult(pair=pair, report=report_runner(pair)) for pair in pairs]


def compute_metrics(results: list[EvaluationResult]) -> EvaluationMetrics:
    if not results:
        return EvaluationMetrics(
            score_in_expected_range_rate=0.0,
            missing_skill_recall=0.0,
            matched_skill_precision=0.0,
            average_match_score=0.0,
        )

    in_range_count = sum(result.score_in_expected_range for result in results)
    expected_missing = 0
    found_missing = 0
    predicted_matched = 0
    correct_matched = 0

    for result in results:
        expected_missing_skills = _skill_set(result.pair.expected_missing_skills)
        actual_missing_skills = _skill_set(result.report.missing_skills)
        expected_matched_skills = _skill_set(result.pair.expected_matched_skills)
        actual_matched_skills = _skill_set(result.report.matched_skills)

        expected_missing += len(expected_missing_skills)
        found_missing += len(expected_missing_skills & actual_missing_skills)
        predicted_matched += len(actual_matched_skills)
        correct_matched += len(expected_matched_skills & actual_matched_skills)

    return EvaluationMetrics(
        score_in_expected_range_rate=round(in_range_count / len(results), 4),
        missing_skill_recall=_safe_rate(found_missing, expected_missing),
        matched_skill_precision=_safe_rate(correct_matched, predicted_matched),
        average_match_score=round(
            sum(result.report.match_score for result in results) / len(results),
            2,
        ),
    )


def evaluation_ranker() -> HybridRanker:
    return HybridRanker(
        report_builder=MatchingReportBuilder(
            semantic_matcher=DeterministicSemanticMatcher(),
            recommendation_engine=NoOpRecommendationEngine(),
        )
    )


def _semantic_terms(text: str) -> set[str]:
    normalized = normalize_skill(text)
    return {
        token
        for token in re.findall(r"[a-z0-9+#]+", normalized)
        if len(token) >= 3 and token not in {"and", "the", "for", "with", "years"}
    }


def _skill_set(skills: list[str]) -> set[str]:
    return {normalize_skill(skill) for skill in skills}


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 4)
