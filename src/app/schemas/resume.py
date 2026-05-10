from pydantic import BaseModel, Field

from app.schemas.extraction import ExtractedProfile


class ResumeInput(BaseModel):
    filename: str | None = None
    text: str = Field(min_length=1)


class ResumeProfile(BaseModel):
    id: str | None = None
    source_filename: str | None = None
    raw_text: str
    extracted: ExtractedProfile = Field(default_factory=ExtractedProfile)
