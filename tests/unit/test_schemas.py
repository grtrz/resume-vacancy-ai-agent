from app.schemas.resume import ResumeInput
from app.schemas.vacancy import VacancyInput


def test_resume_input_requires_text() -> None:
    resume = ResumeInput(text="Python developer with FastAPI experience")

    assert resume.text.startswith("Python")


def test_vacancy_input_accepts_optional_metadata() -> None:
    vacancy = VacancyInput(title="Backend Engineer", text="Python and SQL required")

    assert vacancy.title == "Backend Engineer"
    assert vacancy.company is None
