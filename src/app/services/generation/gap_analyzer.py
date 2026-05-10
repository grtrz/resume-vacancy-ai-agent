from app.schemas.report import GapItem


class GapAnalyzer:
    def analyze(self, missing_skills: list[str]) -> list[GapItem]:
        return [GapItem(category="skill", requirement=skill) for skill in missing_skills]
