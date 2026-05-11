from pydantic import BaseModel, ConfigDict, Field

from app.schemas.extraction import VacancyRequirements
from app.schemas.report import RetrievedExample


class BulletRewriteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_resume_text: str = Field(min_length=1)
    vacancy_requirements: VacancyRequirements = Field(default_factory=VacancyRequirements)
    missing_skills: list[str] = Field(default_factory=list)
    retrieved_examples: list[RetrievedExample] = Field(default_factory=list)


class BulletRewriteSuggestion(BaseModel):
    original_bullet: str | None = None
    rewritten_bullet: str = Field(min_length=1)
    referenced_skills: list[str] = Field(default_factory=list)
    retrieved_example_bullets: list[str] = Field(default_factory=list)
    is_conditional: bool = False
    grounding: str = Field(min_length=1)


class BulletRewriteResult(BaseModel):
    provider: str
    suggestions: list[BulletRewriteSuggestion] = Field(default_factory=list)
