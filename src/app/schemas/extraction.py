from pydantic import BaseModel, Field


class ExperienceRange(BaseModel):
    minimum_years: float | None = Field(default=None, ge=0)
    maximum_years: float | None = Field(default=None, ge=0)


class ExtractedProfile(BaseModel):
    hard_skills: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    experience_years: float | None = Field(default=None, ge=0)
    education: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class VacancyRequirements(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience: ExperienceRange | None = None
    responsibilities: list[str] = Field(default_factory=list)
