from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.report import MatchReportRequest, ResumeVacancyReport
from app.services.extraction.skill_extractor import SkillExtractor
from app.services.matching.hybrid_ranker import HybridRanker
from app.services.parsing.text_cleaner import clean_text

router = APIRouter(prefix="/reports", tags=["reports"])


@lru_cache
def get_skill_extractor() -> SkillExtractor:
    return SkillExtractor()


@lru_cache
def get_hybrid_ranker() -> HybridRanker:
    return HybridRanker()


@router.post("/match", response_model=ResumeVacancyReport)
def match_resume_to_vacancy(
    request: MatchReportRequest,
    extractor: Annotated[SkillExtractor, Depends(get_skill_extractor)],
    ranker: Annotated[HybridRanker, Depends(get_hybrid_ranker)],
) -> ResumeVacancyReport:
    resume_text = clean_text(request.resume_text)
    vacancy_text = clean_text(request.vacancy_text)

    resume_profile = extractor.extract_resume(resume_text)
    vacancy_profile = extractor.extract_vacancy(vacancy_text)

    return ranker.compare(resume_profile, vacancy_profile)
