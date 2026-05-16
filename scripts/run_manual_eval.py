from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from app.schemas.report import (  # noqa: E402
    RecommendationSuggestion,
    ResumeVacancyReport,
    RetrievedExample,
)
from app.schemas.resume import ResumeProfile  # noqa: E402
from app.schemas.vacancy import VacancyProfile  # noqa: E402
from app.services.evaluation.matching_evaluator import DeterministicSemanticMatcher  # noqa: E402
from app.services.extraction.skill_extractor import SkillExtractor  # noqa: E402
from app.services.matching.hybrid_ranker import HybridRanker  # noqa: E402
from app.services.matching.report_builder import MatchingReportBuilder  # noqa: E402
from app.services.parsing.text_cleaner import clean_text  # noqa: E402

DEFAULT_RESUME_PATH = PROJECT_ROOT / "data" / "manual_eval" / "nlp_middle_resume.txt"
DEFAULT_VACANCY_PATHS = (
    PROJECT_ROOT / "data" / "manual_eval" / "nlp_middle_vacancy.txt",
    PROJECT_ROOT / "data" / "manual_eval" / "backend_ml_vacancy.txt",
)


class DeterministicManualRecommendationEngine:
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
        selected_skills = _target_skills(missing_skills, matched_skills or [], limit)
        retrieved_examples = [
            RetrievedExample(
                skill=skill,
                category=_example_category(skill, missing_skills),
                example_bullet=_example_bullet(skill),
                relevance_score=100.0,
            )
            for skill in selected_skills
        ]
        recommendations = [
            RecommendationSuggestion(
                skill=example.skill,
                category=_recommendation_category(example.skill, missing_skills),
                suggestion=_recommendation_text(example.skill, missing_skills),
                example_bullet=example.example_bullet,
            )
            for example in retrieved_examples
        ]
        return recommendations, retrieved_examples


def build_manual_report(resume_text: str, vacancy_text: str) -> ResumeVacancyReport:
    extractor = SkillExtractor()
    ranker = HybridRanker(
        report_builder=MatchingReportBuilder(
            semantic_matcher=DeterministicSemanticMatcher(),
            recommendation_engine=DeterministicManualRecommendationEngine(),
        )
    )
    cleaned_resume_text = clean_text(resume_text)
    cleaned_vacancy_text = clean_text(vacancy_text)
    resume = ResumeProfile(
        raw_text=cleaned_resume_text,
        extracted=extractor.extract_resume(cleaned_resume_text),
    )
    vacancy = VacancyProfile(
        raw_text=cleaned_vacancy_text,
        requirements=extractor.extract_vacancy(cleaned_vacancy_text),
    )
    return ranker.compare(resume, vacancy)


def print_report(vacancy_path: Path, report: ResumeVacancyReport) -> None:
    print(f"\n=== {vacancy_path.name} ===")
    print(f"Match score: {report.match_score:.2f}")
    print(f"Matched skills: {_format_list(report.matched_skills)}")
    print(f"Missing skills: {_format_list(report.missing_skills)}")

    gap_recommendations = [
        recommendation
        for recommendation in report.recommendations
        if recommendation.category == "missing_skill_gap"
    ]
    strengthening_suggestions = [
        recommendation
        for recommendation in report.recommendations
        if recommendation.category == "strengthen_existing_experience"
    ]

    print("Gap recommendations:")
    if not gap_recommendations:
        print("- none")
    for recommendation in gap_recommendations:
        print(f"- {recommendation.skill}: {recommendation.suggestion}")

    print("Strengthening suggestions:")
    if not strengthening_suggestions:
        print("- none")
    for recommendation in strengthening_suggestions:
        print(f"- {recommendation.skill}: {recommendation.suggestion}")

    print("Retrieved examples:")
    if not report.retrieved_examples:
        print("- none")
    for example in report.retrieved_examples:
        print(f"- {example.skill} ({example.relevance_score:.1f}): {example.example_bullet}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic manual matching examples.")
    parser.add_argument(
        "resume",
        nargs="?",
        type=Path,
        default=DEFAULT_RESUME_PATH,
        help="Path to a resume text file.",
    )
    parser.add_argument(
        "vacancies",
        nargs="*",
        type=Path,
        help="One or more vacancy text files.",
    )
    args = parser.parse_args()

    vacancy_paths = args.vacancies or list(DEFAULT_VACANCY_PATHS)
    resume_text = args.resume.read_text(encoding="utf-8")
    print(f"Resume: {args.resume}")
    for vacancy_path in vacancy_paths:
        report = build_manual_report(
            resume_text,
            vacancy_path.read_text(encoding="utf-8"),
        )
        print_report(vacancy_path, report)
    return 0


def _format_list(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _example_bullet(skill: str) -> str:
    examples = {
        "airflow": "Scheduled and monitored data pipelines with Airflow DAGs.",
        "ci/cd": "Maintained CI/CD checks for tests, linting, and deployment gates.",
        "kubernetes": "Supported Kubernetes deployments with rollout and health checks.",
        "ml engineering": "Built repeatable training and serving workflows for ML systems.",
        "mlops": "Improved model delivery with versioning, validation, and monitoring.",
        "spark": "Processed large datasets with Spark batch jobs.",
    }
    return examples.get(skill, f"Demonstrated production experience with {skill}.")


def _target_skills(
    missing_skills: list[str],
    matched_skills: list[str],
    limit: int,
) -> list[str]:
    if missing_skills:
        return [*missing_skills[:limit], *matched_skills[: max(0, limit - len(missing_skills))]]
    return matched_skills[:limit]


def _recommendation_category(skill: str, missing_skills: list[str]) -> str:
    if skill in set(missing_skills):
        return "missing_skill_gap"
    return "strengthen_existing_experience"


def _example_category(skill: str, missing_skills: list[str]) -> str:
    if skill in set(missing_skills):
        return "manual_eval_gap"
    return "manual_eval_strengthening"


def _recommendation_text(skill: str, missing_skills: list[str]) -> str:
    if skill in set(missing_skills):
        return (
            f"Address '{skill}' only if the resume has real supporting project or "
            "production evidence."
        )
    return (
        f"Strengthen existing {skill} experience by adding measurable scope, impact, "
        "or reliability details already supported by the resume."
    )


if __name__ == "__main__":
    raise SystemExit(main())
