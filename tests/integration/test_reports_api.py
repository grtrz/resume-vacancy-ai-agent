from fastapi.testclient import TestClient

from app.main import app


def test_match_report_endpoint_returns_structured_report() -> None:
    client = TestClient(app)

    response = client.post(
        "/reports/match",
        json={
            "resume_text": """
            Skills
            Python, FastAPI, PostgreSQL, Docker, Pytest

            Experience
            6+ years of experience building backend REST APIs with SQL.

            Projects
            Built PostgreSQL services with FastAPI and Docker.
            """,
            "vacancy_text": """
            Skills
            Python, FastAPI, PostgreSQL

            Experience
            At least 5 years of backend experience building REST APIs.
            """,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_score"] >= 90.0
    assert payload["score_breakdown"]["skills_overlap"] == 100.0
    assert payload["score_breakdown"]["experience_match"] == 100.0
    assert set(payload["matched_skills"]) == {
        "fastapi",
        "postgresql",
        "python",
        "rest api",
    }
    assert payload["missing_skills"] == []
    assert payload["gaps"] == []


def test_match_report_endpoint_rejects_blank_text() -> None:
    client = TestClient(app)

    response = client.post(
        "/reports/match",
        json={
            "resume_text": " ",
            "vacancy_text": "Skills\nPython",
        },
    )

    assert response.status_code == 422


def test_match_report_endpoint_rejects_unknown_fields() -> None:
    client = TestClient(app)

    response = client.post(
        "/reports/match",
        json={
            "resume_text": "Skills\nPython",
            "vacancy_text": "Skills\nPython",
            "file": "resume.pdf",
        },
    )

    assert response.status_code == 422
