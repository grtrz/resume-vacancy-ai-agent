from pydantic import BaseModel, Field


class AgentState(BaseModel):
    resume_text: str | None = None
    vacancy_text: str | None = None
    messages: list[str] = Field(default_factory=list)
