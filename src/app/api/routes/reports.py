from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.schemas.report import MatchReportRequest, ResumeVacancyReport
from app.schemas.resume import ResumeProfile
from app.schemas.vacancy import VacancyProfile
from app.services.extraction.skill_extractor import SkillExtractor
from app.services.matching.hybrid_ranker import HybridRanker
from app.services.parsing.base import ParsingError
from app.services.parsing.parser_factory import parser_for_upload
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
    return _build_report(request.resume_text, request.vacancy_text, extractor, ranker)


@router.post("/match-file", response_model=ResumeVacancyReport)
async def match_resume_file_to_vacancy(
    resume_file: Annotated[UploadFile, File()],
    vacancy_text: Annotated[str, Form()],
    extractor: Annotated[SkillExtractor, Depends(get_skill_extractor)],
    ranker: Annotated[HybridRanker, Depends(get_hybrid_ranker)],
    enable_bullet_rewriting: Annotated[bool, Form()] = False,
) -> ResumeVacancyReport:
    _ = enable_bullet_rewriting
    if not vacancy_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vacancy_text must not be blank.",
        )

    parser = parser_for_upload(resume_file.filename, resume_file.content_type)
    if parser is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported resume file type.",
        )

    content = await resume_file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="resume_file must not be empty.",
        )

    try:
        resume_text = parser.parse(content)
    except ParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not resume_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="resume_file did not contain extractable text.",
        )

    return _build_report(resume_text, vacancy_text, extractor, ranker)


def _build_report(
    resume_text: str,
    vacancy_text: str,
    extractor: SkillExtractor,
    ranker: HybridRanker,
) -> ResumeVacancyReport:
    resume_text = clean_text(resume_text)
    vacancy_text = clean_text(vacancy_text)

    resume_profile = ResumeProfile(
        raw_text=resume_text,
        extracted=extractor.extract_resume(resume_text),
    )
    vacancy_profile = VacancyProfile(
        raw_text=vacancy_text,
        requirements=extractor.extract_vacancy(vacancy_text),
    )

    return ranker.compare(resume_profile, vacancy_profile)
