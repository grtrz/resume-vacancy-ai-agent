import re

from app.schemas.extraction import ExtractedProfile, VacancyRequirements
from app.services.extraction.normalizer import SKILL_ALIASES, fold_for_matching, normalize_skill
from app.services.extraction.regex_extractors import (
    extract_experience_range,
    extract_years_of_experience,
)
from app.services.extraction.section_extractor import extract_sections

DEFAULT_SKILL_DICTIONARY = {
    "alembic",
    "airflow",
    "aws",
    "azure",
    "celery",
    "ci/cd",
    "css",
    "data engineering",
    "data pipelines",
    "django",
    "docker",
    "embeddings",
    "fastapi",
    "faiss",
    "flask",
    "gcp",
    "generative ai",
    "git",
    "graphql",
    "html",
    "hugging face",
    "hugging face transformers",
    "javascript",
    "kafka",
    "kubernetes",
    "langgraph",
    "linux",
    "llm",
    "machine learning",
    "ml engineering",
    "mlops",
    "mongodb",
    "mysql",
    "natural language processing",
    "node.js",
    "nlp",
    "numpy",
    "pandas",
    "postgresql",
    "pydantic",
    "pytest",
    "python",
    "pytorch",
    "qdrant",
    "rabbitmq",
    "rag",
    "react",
    "redis",
    "rest api",
    "ruff",
    "scikit-learn",
    "sentence-transformers",
    "spark",
    "sql",
    "sqlalchemy",
    "sqlite",
    "tensorflow",
    "typescript",
    "vector databases",
}

_FRAMEWORKS = {
    "django",
    "fastapi",
    "flask",
    "hugging face transformers",
    "langgraph",
    "pydantic",
    "pytorch",
    "react",
    "scikit-learn",
    "sentence-transformers",
    "sqlalchemy",
    "tensorflow",
}

_TOOLS = {
    "alembic",
    "aws",
    "azure",
    "airflow",
    "ci/cd",
    "docker",
    "faiss",
    "gcp",
    "git",
    "kafka",
    "kubernetes",
    "linux",
    "mlops",
    "pytest",
    "qdrant",
    "rabbitmq",
    "redis",
    "ruff",
    "spark",
    "vector databases",
}


def _compile_skill_pattern(skill: str) -> re.Pattern[str]:
    folded = re.escape(fold_for_matching(skill))
    return re.compile(rf"(?<![a-z0-9+#]){folded}(?![a-z0-9+#])")


def _content_lines(section_text: str) -> list[str]:
    return [line.strip(" -\t") for line in section_text.splitlines() if line.strip(" -\t")]


class SkillExtractor:
    def __init__(self, skill_dictionary: set[str] | None = None) -> None:
        dictionary = skill_dictionary or DEFAULT_SKILL_DICTIONARY
        self._skills = {normalize_skill(skill) for skill in dictionary}
        self._patterns = {
            skill: tuple(
                _compile_skill_pattern(term) for term in sorted(self._search_terms_for_skill(skill))
            )
            for skill in sorted(self._skills)
        }

    def _search_terms_for_skill(self, skill: str) -> set[str]:
        terms = {skill}
        terms.update(alias for alias, canonical in SKILL_ALIASES.items() if canonical == skill)
        return terms

    def extract_skills(self, text: str) -> list[str]:
        folded_text = fold_for_matching(text)
        matches = [
            skill
            for skill, patterns in self._patterns.items()
            if any(pattern.search(folded_text) for pattern in patterns)
        ]
        return sorted(matches)

    def extract(self, text: str) -> ExtractedProfile:
        return self.extract_resume(text)

    def extract_resume(self, text: str) -> ExtractedProfile:
        sections = extract_sections(text)
        skills = self.extract_skills(text)
        return ExtractedProfile(
            hard_skills=skills,
            frameworks=sorted(skill for skill in skills if skill in _FRAMEWORKS),
            tools=sorted(skill for skill in skills if skill in _TOOLS),
            experience_years=extract_years_of_experience(text),
            education=_content_lines(sections.education),
            projects=_content_lines(sections.projects),
            responsibilities=_content_lines(sections.experience),
            sections=sections.non_empty(),
        )

    def extract_vacancy(self, text: str) -> VacancyRequirements:
        sections = extract_sections(text)
        return VacancyRequirements(
            required_skills=self.extract_skills(text),
            experience=extract_experience_range(text),
            responsibilities=_content_lines(sections.experience),
            sections=sections.non_empty(),
        )
