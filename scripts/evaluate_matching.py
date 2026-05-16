from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from app.services.evaluation.matching_evaluator import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    EvaluationMetrics,
    EvaluationResult,
    compute_metrics,
    evaluate_pairs,
    load_evaluation_pairs,
)


def print_results(results: list[EvaluationResult], metrics: EvaluationMetrics) -> None:
    for result in results:
        status = "PASS" if result.score_in_expected_range else "FAIL"
        expected_range = (
            f"{result.pair.expected_min_score:.1f}-{result.pair.expected_max_score:.1f}"
        )
        print(
            f"{status} {result.pair.id}: "
            f"score={result.report.match_score:.2f} expected={expected_range} "
            f"missing={result.report.missing_skills} matched={result.report.matched_skills}"
        )

    print("\nMetrics")
    print(json.dumps(metrics.__dict__, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate resume-vacancy matching quality.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to evaluation JSON dataset.",
    )
    args = parser.parse_args()

    results = evaluate_pairs(load_evaluation_pairs(args.dataset))
    print_results(results, compute_metrics(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
