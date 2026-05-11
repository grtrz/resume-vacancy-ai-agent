from pydantic import BaseModel, ConfigDict, Field, field_validator


class MatchReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_text: str = Field(min_length=1)
    vacancy_text: str = Field(min_length=1)

    @field_validator("resume_text", "vacancy_text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "Text must not be blank."
            raise ValueError(msg)
        return value


class GapItem(BaseModel):
    category: str
    requirement: str
    evidence: str | None = None
    recommendation: str | None = None


class MatchScoreBreakdown(BaseModel):
    skills_overlap: float = Field(default=0.0, ge=0, le=100)
    experience_match: float = Field(default=0.0, ge=0, le=100)
    keyword_relevance: float = Field(default=0.0, ge=0, le=100)
    coverage_bonus: float = Field(default=0.0, ge=0, le=100)


class ResumeVacancyReport(BaseModel):
    resume_id: str | None = None
    vacancy_id: str | None = None
    match_score: float = Field(ge=0, le=100)
    score_breakdown: MatchScoreBreakdown = Field(default_factory=MatchScoreBreakdown)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    gaps: list[GapItem] = Field(default_factory=list)
    improved_bullets: list[str] = Field(default_factory=list)
