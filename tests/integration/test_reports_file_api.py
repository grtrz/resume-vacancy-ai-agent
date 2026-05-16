from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.api.routes.reports import get_hybrid_ranker
from app.main import app
from app.services.matching.hybrid_ranker import HybridRanker
from app.services.matching.report_builder import MatchingReportBuilder


class StaticSemanticMatcher:
    def compare(self, left: str, right: str) -> float:
        return 100.0 if left and right else 0.0


def get_test_hybrid_ranker() -> HybridRanker:
    return HybridRanker(
        report_builder=MatchingReportBuilder(semantic_matcher=StaticSemanticMatcher())
    )


@contextmanager
def reports_client() -> Iterator[TestClient]:
    app.dependency_overrides[get_hybrid_ranker] = get_test_hybrid_ranker
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_match_file_endpoint_accepts_txt_upload() -> None:
    with reports_client() as client:
        response = client.post(
            "/reports/match-file",
            data={
                "vacancy_text": """
                Skills
                Python, FastAPI, PostgreSQL

                Experience
                At least 5 years of backend experience building REST APIs.
                """,
            },
            files={
                "resume_file": (
                    "resume.txt",
                    b"""
                    Skills
                    Python, FastAPI, PostgreSQL, Docker, Pytest

                    Experience
                    6+ years of experience building backend REST APIs with SQL.
                    """,
                    "text/plain",
                )
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_score"] >= 90.0
    assert payload["score_breakdown"]["skills_overlap"] == 100.0
    assert set(payload["matched_skills"]) == {
        "fastapi",
        "postgresql",
        "python",
        "rest api",
    }


def test_match_file_endpoint_rejects_unsupported_file_type() -> None:
    with reports_client() as client:
        response = client.post(
            "/reports/match-file",
            data={"vacancy_text": "Skills\nPython"},
            files={
                "resume_file": (
                    "resume.rtf",
                    b"{\\rtf1 Skills Python}",
                    "application/rtf",
                )
            },
        )

    assert response.status_code == 400


def test_match_file_endpoint_rejects_empty_file() -> None:
    with reports_client() as client:
        response = client.post(
            "/reports/match-file",
            data={"vacancy_text": "Skills\nPython"},
            files={"resume_file": ("resume.txt", b"", "text/plain")},
        )

    assert response.status_code == 400


def test_match_file_endpoint_rejects_empty_vacancy_text() -> None:
    with reports_client() as client:
        response = client.post(
            "/reports/match-file",
            data={"vacancy_text": " "},
            files={
                "resume_file": (
                    "resume.txt",
                    b"Skills\nPython",
                    "text/plain",
                )
            },
        )

    assert response.status_code in {400, 422}
