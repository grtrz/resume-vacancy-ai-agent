from pydantic import BaseModel, ConfigDict, Field

from app.schemas.extraction import ExtractedProfile, VacancyRequirements
from app.schemas.generation import BulletRewriteResult
from app.schemas.report import (
    MatchScoreBreakdown,
    RecommendationSuggestion,
    ResumeVacancyReport,
    RetrievedExample,
)


class WorkflowState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_text: str
    vacancy_text: str
    enable_bullet_rewriting: bool = False

    cleaned_resume_text: str = ""
    cleaned_vacancy_text: str = ""
    resume_profile: ExtractedProfile | None = None
    vacancy_requirements: VacancyRequirements | None = None

    semantic_similarity: float = Field(default=0.0, ge=0, le=100)
    score_breakdown: MatchScoreBreakdown = Field(default_factory=MatchScoreBreakdown)
    match_score: float = Field(default=0.0, ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    retrieved_examples: list[RetrievedExample] = Field(default_factory=list)
    recommendations: list[RecommendationSuggestion] = Field(default_factory=list)
    bullet_rewrite_result: BulletRewriteResult | None = None
    report: ResumeVacancyReport | None = None

    completed_nodes: list[str] = Field(default_factory=list)


AgentState = WorkflowState
