from collections.abc import Iterable

from app.schemas.extraction import ExperienceRange, ExtractedProfile, VacancyRequirements
from app.schemas.report import GapItem, MatchScoreBreakdown, ResumeVacancyReport
from app.schemas.resume import ResumeProfile
from app.schemas.vacancy import VacancyProfile
from app.services.matching.scoring import (
    coverage_bonus_score,
    experience_match_score,
    keyword_relevance_score,
    matched_skills,
    missing_skills,
    skill_overlap_score,
    weighted_final_score,
)


class MatchingReportBuilder:
    def build(
        self,
        resume: ResumeProfile | ExtractedProfile,
        vacancy: VacancyProfile | VacancyRequirements,
    ) -> ResumeVacancyReport:
        resume_profile = _resume_extracted_profile(resume)
        vacancy_requirements = _vacancy_requirements(vacancy)

        resume_skills = _resume_skills(resume_profile)
        required_skills = vacancy_requirements.required_skills
        preferred_skills = vacancy_requirements.preferred_skills
        vacancy_skills = [*required_skills, *preferred_skills]
        experience = vacancy_requirements.experience or ExperienceRange()

        skills_overlap = skill_overlap_score(resume_skills, required_skills)
        experience_match = experience_match_score(
            resume_profile.experience_years,
            experience.minimum_years,
            experience.maximum_years,
        )
        keyword_relevance = keyword_relevance_score(
            _resume_keyword_terms(resume_profile),
            _vacancy_keyword_terms(vacancy_requirements),
        )
        coverage_bonus = coverage_bonus_score(resume_skills, required_skills, preferred_skills)
        match_score = weighted_final_score(
            skills_overlap,
            experience_match,
            keyword_relevance,
            coverage_bonus,
        )

        missing = missing_skills(resume_skills, required_skills)

        return ResumeVacancyReport(
            resume_id=resume.id if isinstance(resume, ResumeProfile) else None,
            vacancy_id=vacancy.id if isinstance(vacancy, VacancyProfile) else None,
            match_score=match_score,
            score_breakdown=MatchScoreBreakdown(
                skills_overlap=skills_overlap,
                experience_match=experience_match,
                keyword_relevance=keyword_relevance,
                coverage_bonus=coverage_bonus,
            ),
            matched_skills=matched_skills(resume_skills, vacancy_skills),
            missing_skills=missing,
            gaps=[GapItem(category="skill", requirement=skill) for skill in missing],
        )


def build_matching_report(
    resume: ResumeProfile | ExtractedProfile,
    vacancy: VacancyProfile | VacancyRequirements,
) -> ResumeVacancyReport:
    return MatchingReportBuilder().build(resume, vacancy)


def _resume_extracted_profile(resume: ResumeProfile | ExtractedProfile) -> ExtractedProfile:
    if isinstance(resume, ResumeProfile):
        return resume.extracted
    return resume


def _vacancy_requirements(vacancy: VacancyProfile | VacancyRequirements) -> VacancyRequirements:
    if isinstance(vacancy, VacancyProfile):
        return vacancy.requirements
    return vacancy


def _resume_skills(profile: ExtractedProfile) -> list[str]:
    return sorted({*profile.hard_skills, *profile.frameworks, *profile.tools})


def _resume_keyword_terms(profile: ExtractedProfile) -> Iterable[str]:
    return (
        *profile.hard_skills,
        *profile.frameworks,
        *profile.tools,
        *profile.education,
        *profile.projects,
        *profile.responsibilities,
        *profile.achievements,
        *profile.sections.values(),
    )


def _vacancy_keyword_terms(requirements: VacancyRequirements) -> Iterable[str]:
    return (
        *requirements.required_skills,
        *requirements.preferred_skills,
        *requirements.responsibilities,
        *requirements.sections.values(),
    )
