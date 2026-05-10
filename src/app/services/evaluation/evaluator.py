from app.schemas.report import ResumeVacancyReport


class RecommendationEvaluator:
    def evaluate(self, report: ResumeVacancyReport) -> dict[str, float]:
        return {"placeholder_score": report.match_score}
