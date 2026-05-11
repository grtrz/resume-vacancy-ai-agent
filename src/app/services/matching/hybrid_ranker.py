from app.schemas.extraction import ExtractedProfile, VacancyRequirements
from app.schemas.report import ResumeVacancyReport
from app.schemas.resume import ResumeProfile
from app.schemas.vacancy import VacancyProfile
from app.services.matching.report_builder import MatchingReportBuilder


class HybridRanker:
    def __init__(self, report_builder: MatchingReportBuilder | None = None) -> None:
        self._report_builder = report_builder or MatchingReportBuilder()

    def compare(
        self,
        resume: ResumeProfile | ExtractedProfile,
        vacancy: VacancyProfile | VacancyRequirements,
    ) -> ResumeVacancyReport:
        return self._report_builder.build(resume, vacancy)

    def rank_vacancies(
        self,
        resume: ResumeProfile | ExtractedProfile,
        vacancies: list[VacancyProfile | VacancyRequirements],
    ) -> list[ResumeVacancyReport]:
        return self.rank([self.compare(resume, vacancy) for vacancy in vacancies])

    def rank(self, reports: list[ResumeVacancyReport]) -> list[ResumeVacancyReport]:
        return sorted(reports, key=lambda report: report.match_score, reverse=True)
