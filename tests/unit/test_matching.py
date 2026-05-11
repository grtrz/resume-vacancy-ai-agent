from app.schemas.extraction import ExperienceRange, ExtractedProfile, VacancyRequirements
from app.schemas.resume import ResumeProfile
from app.schemas.vacancy import VacancyProfile
from app.services.matching.hybrid_ranker import HybridRanker
from app.services.matching.report_builder import MatchingReportBuilder


class StaticSemanticMatcher:
    def __init__(self, score: float = 100.0) -> None:
        self._score = score

    def compare(self, left: str, right: str) -> float:
        return self._score if left and right else 0.0


def _builder(semantic_score: float = 100.0) -> MatchingReportBuilder:
    return MatchingReportBuilder(semantic_matcher=StaticSemanticMatcher(semantic_score))


def test_matching_report_for_strong_match() -> None:
    resume = ExtractedProfile(
        hard_skills=["Python", "FastAPI", "SQL", "Docker", "Pytest"],
        experience_years=6,
        projects=["Built PostgreSQL services and REST APIs"],
        responsibilities=["Built backend REST APIs with FastAPI and SQL"],
    )
    vacancy = VacancyRequirements(
        required_skills=["python", "fastapi", "sql"],
        preferred_skills=["docker", "pytest"],
        experience=ExperienceRange(minimum_years=5, maximum_years=8),
        responsibilities=["Build backend REST APIs with PostgreSQL"],
    )

    report = _builder().build(resume, vacancy)

    assert report.match_score >= 90.0
    assert report.score_breakdown.skills_overlap == 100.0
    assert report.score_breakdown.experience_match == 100.0
    assert report.score_breakdown.coverage_bonus == 100.0
    assert report.score_breakdown.semantic_similarity == 100.0
    assert report.matched_skills == ["docker", "fastapi", "pytest", "python", "sql"]
    assert report.missing_skills == []


def test_matching_report_for_weak_match() -> None:
    resume = ExtractedProfile(
        hard_skills=["html", "css"],
        experience_years=1,
        projects=["Built static marketing pages"],
    )
    vacancy = VacancyRequirements(
        required_skills=["python", "fastapi", "sql"],
        experience=ExperienceRange(minimum_years=5),
        responsibilities=["Build backend APIs and database services"],
    )

    report = _builder(semantic_score=0.0).build(resume, vacancy)

    assert report.match_score < 25.0
    assert report.score_breakdown.skills_overlap == 0.0
    assert report.matched_skills == []
    assert report.missing_skills == ["fastapi", "python", "sql"]


def test_matching_report_lists_missing_required_skills() -> None:
    resume = ExtractedProfile(hard_skills=["Python"], experience_years=4)
    vacancy = VacancyRequirements(
        required_skills=["Python", "SQL", "Docker"],
        experience=ExperienceRange(minimum_years=3),
    )

    report = _builder().build(resume, vacancy)

    assert report.score_breakdown.skills_overlap == 33.33
    assert report.matched_skills == ["python"]
    assert report.missing_skills == ["docker", "sql"]
    assert [gap.requirement for gap in report.gaps] == ["docker", "sql"]


def test_experience_mismatch_lowers_score() -> None:
    vacancy = VacancyRequirements(
        required_skills=["Python", "FastAPI", "SQL"],
        experience=ExperienceRange(minimum_years=5),
    )
    junior_resume = ExtractedProfile(
        hard_skills=["Python", "FastAPI", "SQL"],
        experience_years=1,
    )
    senior_resume = ExtractedProfile(
        hard_skills=["Python", "FastAPI", "SQL"],
        experience_years=5,
    )
    builder = _builder()

    junior_report = builder.build(junior_resume, vacancy)
    senior_report = builder.build(senior_resume, vacancy)

    assert junior_report.score_breakdown.experience_match == 20.0
    assert senior_report.score_breakdown.experience_match == 100.0
    assert junior_report.match_score < senior_report.match_score


def test_hybrid_ranker_builds_and_sorts_reports() -> None:
    resume = ResumeProfile(
        id="resume-1",
        raw_text="",
        extracted=ExtractedProfile(hard_skills=["Python", "FastAPI"], experience_years=4),
    )
    strong_vacancy = VacancyProfile(
        id="vacancy-strong",
        raw_text="",
        requirements=VacancyRequirements(
            required_skills=["Python", "FastAPI"],
            experience=ExperienceRange(minimum_years=3),
        ),
    )
    weak_vacancy = VacancyProfile(
        id="vacancy-weak",
        raw_text="",
        requirements=VacancyRequirements(
            required_skills=["React", "TypeScript"],
            experience=ExperienceRange(minimum_years=6),
        ),
    )

    ranker = HybridRanker(report_builder=_builder())

    reports = ranker.rank_vacancies(resume, [weak_vacancy, strong_vacancy])

    assert [report.vacancy_id for report in reports] == ["vacancy-strong", "vacancy-weak"]
