from app.schemas.extraction import ExtractedProfile, VacancyRequirements
from app.services.extraction.normalizer import normalize_skill
from app.services.extraction.regex_extractors import (
    extract_experience_range,
    extract_years_of_experience,
)
from app.services.extraction.section_extractor import extract_sections
from app.services.extraction.skill_extractor import SkillExtractor


def test_skill_extraction_uses_dictionary_matching() -> None:
    text = "Built backend services with Python, FastAPI, PostgreSQL, and Docker."

    skills = SkillExtractor().extract_skills(text)

    assert skills == ["docker", "fastapi", "postgresql", "python"]


def test_skill_aliases_are_normalized() -> None:
    text = "Model training with torch, deployed on k8s with JS clients and postgres."

    skills = SkillExtractor().extract_skills(text)

    assert "pytorch" in skills
    assert "torch" not in skills
    assert "kubernetes" in skills
    assert "javascript" in skills
    assert "postgresql" in skills
    assert normalize_skill("PyTorch") == "pytorch"
    assert normalize_skill("torch") == "pytorch"
    assert normalize_skill("llms") == "llm"
    assert normalize_skill("genai") == "generative ai"
    assert normalize_skill("hf") == "hugging face"
    assert normalize_skill("transformers") == "hugging face transformers"
    assert normalize_skill("sbert") == "sentence-transformers"


def test_ml_nlp_backend_skills_are_extracted() -> None:
    text = """
    Built RAG systems with LLM orchestration, NLP preprocessing, embeddings,
    sentence-transformers, Qdrant, FAISS, Hugging Face Transformers, PyTorch,
    Airflow data pipelines, Spark data engineering, and MLOps CI/CD workflows.
    """

    skills = SkillExtractor().extract_skills(text)

    assert set(skills) >= {
        "airflow",
        "ci/cd",
        "data engineering",
        "data pipelines",
        "embeddings",
        "faiss",
        "hugging face transformers",
        "llm",
        "mlops",
        "nlp",
        "pytorch",
        "qdrant",
        "rag",
        "sentence-transformers",
        "spark",
    }


def test_ml_nlp_aliases_are_extracted_as_canonical_skills() -> None:
    text = (
        "Used HF transformers, SBERT embeddings, k8s, postgres, torch, genai, "
        "llms, and vector db search."
    )

    skills = SkillExtractor().extract_skills(text)

    assert "hugging face" in skills
    assert "hugging face transformers" in skills
    assert "sentence-transformers" in skills
    assert "embeddings" in skills
    assert "kubernetes" in skills
    assert "postgresql" in skills
    assert "pytorch" in skills
    assert "generative ai" in skills
    assert "llm" in skills
    assert "vector databases" in skills


def test_generic_ml_backend_words_do_not_create_false_positive_skills() -> None:
    text = """
    Built models for data products and backend systems with strong ownership,
    reliable delivery, stakeholder communication, and production support.
    """

    skills = SkillExtractor().extract_skills(text)

    assert skills == []


def test_years_of_experience_are_extracted_from_regex_patterns() -> None:
    text = "Senior backend engineer with 5+ years of experience and 3 years with SQL."

    assert extract_years_of_experience(text) == 5


def test_experience_range_is_extracted_for_vacancies() -> None:
    experience = extract_experience_range("Required: 2-4 years of Python experience.")

    assert experience is not None
    assert experience.minimum_years == 2
    assert experience.maximum_years == 4


def test_basic_sections_are_detected() -> None:
    text = """
Skills
Python, FastAPI, SQL

Experience:
Built APIs

Education
BS Computer Science

Projects
Resume matcher
"""

    sections = extract_sections(text)

    assert sections.skills == "Python, FastAPI, SQL"
    assert sections.experience == "Built APIs"
    assert sections.education == "BS Computer Science"
    assert sections.projects == "Resume matcher"


def test_resume_extraction_returns_structured_model() -> None:
    result = SkillExtractor().extract_resume(
        """
Skills
Python, torch, SQL
Experience
5 years of experience building APIs
Education
MSc Computer Science
Projects
Ranking service
"""
    )

    assert isinstance(result, ExtractedProfile)
    assert set(result.hard_skills) == {"pytorch", "python", "sql"}
    assert result.experience_years == 5
    assert result.education == ["MSc Computer Science"]
    assert result.projects == ["Ranking service"]
    assert set(result.sections) == {"skills", "experience", "education", "projects"}


def test_vacancy_extraction_returns_structured_model() -> None:
    result = SkillExtractor().extract_vacancy(
        """
Skills
Python, FastAPI, PostgreSQL
Experience
At least 3 years of backend experience
"""
    )

    assert isinstance(result, VacancyRequirements)
    assert result.required_skills == ["fastapi", "postgresql", "python"]
    assert result.experience is not None
    assert result.experience.minimum_years == 3
