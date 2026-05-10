from pydantic import BaseModel, Field

from app.schemas.extraction import VacancyRequirements


class VacancyInput(BaseModel):
    title: str | None = None
    company: str | None = None
    text: str = Field(min_length=1)


class VacancyProfile(BaseModel):
    id: str | None = None
    title: str | None = None
    company: str | None = None
    raw_text: str
    requirements: VacancyRequirements = Field(default_factory=VacancyRequirements)
