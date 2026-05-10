from pydantic import BaseModel, Field


class GapItem(BaseModel):
    category: str
    requirement: str
    evidence: str | None = None
    recommendation: str | None = None


class ResumeVacancyReport(BaseModel):
    resume_id: str | None = None
    vacancy_id: str | None = None
    match_score: float = Field(ge=0, le=1)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    gaps: list[GapItem] = Field(default_factory=list)
    improved_bullets: list[str] = Field(default_factory=list)
