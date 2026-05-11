import re
from collections.abc import Iterable

from app.services.extraction.normalizer import fold_for_matching, normalize_skill
from app.services.rag.embeddings import EmbeddingService

SKILL_WEIGHT = 0.35
EXPERIENCE_WEIGHT = 0.20
KEYWORD_WEIGHT = 0.15
COVERAGE_WEIGHT = 0.10
SEMANTIC_WEIGHT = 0.20

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "our",
    "the",
    "to",
    "with",
    "you",
    "your",
}


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def normalized_skill_set(skills: Iterable[str]) -> set[str]:
    return {normalized for skill in skills if (normalized := normalize_skill(skill))}


def matched_skills(resume_skills: Iterable[str], vacancy_skills: Iterable[str]) -> list[str]:
    resume_set = normalized_skill_set(resume_skills)
    vacancy_set = normalized_skill_set(vacancy_skills)
    return sorted(resume_set & vacancy_set)


def missing_skills(resume_skills: Iterable[str], required_skills: Iterable[str]) -> list[str]:
    resume_set = normalized_skill_set(resume_skills)
    required_set = normalized_skill_set(required_skills)
    return sorted(required_set - resume_set)


def skill_overlap_score(resume_skills: Iterable[str], required_skills: Iterable[str]) -> float:
    required_set = normalized_skill_set(required_skills)
    if not required_set:
        return 0.0

    resume_set = normalized_skill_set(resume_skills)
    return clamp_score(len(resume_set & required_set) / len(required_set) * 100)


def experience_match_score(
    resume_years: float | None,
    minimum_years: float | None = None,
    maximum_years: float | None = None,
) -> float:
    if minimum_years is None and maximum_years is None:
        return 100.0
    if resume_years is None:
        return 0.0

    if minimum_years is not None and resume_years < minimum_years:
        if minimum_years == 0:
            return 100.0
        return clamp_score(resume_years / minimum_years * 100)

    if maximum_years is not None and resume_years > maximum_years:
        if resume_years == 0:
            return 100.0
        return clamp_score(maximum_years / resume_years * 100)

    return 100.0


def keyword_relevance_score(resume_terms: Iterable[str], vacancy_terms: Iterable[str]) -> float:
    vacancy_tokens = _keyword_tokens(vacancy_terms)
    if not vacancy_tokens:
        return 0.0

    resume_tokens = _keyword_tokens(resume_terms)
    return clamp_score(len(resume_tokens & vacancy_tokens) / len(vacancy_tokens) * 100)


def coverage_bonus_score(
    resume_skills: Iterable[str],
    required_skills: Iterable[str],
    preferred_skills: Iterable[str],
) -> float:
    vacancy_skills = normalized_skill_set([*required_skills, *preferred_skills])
    if not vacancy_skills:
        return 0.0

    resume_set = normalized_skill_set(resume_skills)
    return clamp_score(len(resume_set & vacancy_skills) / len(vacancy_skills) * 100)


def semantic_similarity_score(
    resume_text: str,
    vacancy_text: str,
    embedding_service: EmbeddingService | None = None,
) -> float:
    service = embedding_service or EmbeddingService()
    return service.similarity(resume_text, vacancy_text)


def weighted_final_score(
    skills_overlap: float,
    experience_match: float,
    keyword_relevance: float,
    coverage_bonus: float,
    semantic_similarity: float,
) -> float:
    return clamp_score(
        skills_overlap * SKILL_WEIGHT
        + experience_match * EXPERIENCE_WEIGHT
        + keyword_relevance * KEYWORD_WEIGHT
        + coverage_bonus * COVERAGE_WEIGHT
        + semantic_similarity * SEMANTIC_WEIGHT
    )


def _keyword_tokens(values: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        folded = fold_for_matching(value)
        tokens.update(
            token
            for token in re.findall(r"[a-z0-9+#]+", folded)
            if token not in _STOPWORDS and len(token) >= 2
        )
    return tokens
