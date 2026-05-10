from app.schemas.report import ResumeVacancyReport


class HybridRanker:
    def rank(self, reports: list[ResumeVacancyReport]) -> list[ResumeVacancyReport]:
        return sorted(reports, key=lambda report: report.match_score, reverse=True)
