from __future__ import annotations

from pydantic import BaseModel

from app.services.extraction.normalizer import normalize_token

SECTION_NAMES = ("skills", "experience", "education", "projects")

_SECTION_ALIASES = {
    "skills": {"skills", "technical skills", "technologies", "stack", "core skills"},
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "career history",
    },
    "education": {"education", "academic background", "certifications"},
    "projects": {"projects", "selected projects", "portfolio"},
}

_ALIAS_TO_SECTION = {
    alias: section for section, aliases in _SECTION_ALIASES.items() for alias in aliases
}


class ExtractedSections(BaseModel):
    skills: str = ""
    experience: str = ""
    education: str = ""
    projects: str = ""

    def non_empty(self) -> dict[str, str]:
        return {
            section: value
            for section, value in self.model_dump().items()
            if section in SECTION_NAMES and value
        }


def _line_section_name(line: str) -> str | None:
    normalized = normalize_token(line.rstrip(":"))
    return _ALIAS_TO_SECTION.get(normalized)


def extract_sections(text: str) -> ExtractedSections:
    current_section: str | None = None
    collected: dict[str, list[str]] = {section: [] for section in SECTION_NAMES}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        section = _line_section_name(line)
        if section is not None:
            current_section = section
            continue

        if current_section is not None:
            collected[current_section].append(line)

    return ExtractedSections(
        **{section: "\n".join(lines).strip() for section, lines in collected.items()}
    )
