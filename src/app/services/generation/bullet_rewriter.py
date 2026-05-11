import json

from app.schemas.generation import (
    BulletRewriteInput,
    BulletRewriteResult,
    BulletRewriteSuggestion,
)
from app.schemas.report import RetrievedExample
from app.services.extraction.normalizer import normalize_skill
from app.services.generation.llm_provider import LLMProvider, configured_llm_provider


class BulletRewriter:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        use_configured_provider: bool = True,
    ) -> None:
        self._provider = (
            provider
            if provider is not None or not use_configured_provider
            else configured_llm_provider()
        )

    def rewrite(self, request: BulletRewriteInput) -> BulletRewriteResult:
        if self._provider is None:
            return BulletRewriteResult(
                provider="deterministic_rule_based",
                suggestions=_fallback_suggestions(request),
            )

        payload = self._provider.generate_json(
            _system_prompt(),
            _user_prompt(request),
        )
        result = BulletRewriteResult.model_validate(
            {
                "provider": self._provider.provider_name,
                "suggestions": payload.get("suggestions", []),
            }
        )
        return BulletRewriteResult(
            provider=result.provider,
            suggestions=[
                _sanitize_suggestion(suggestion, request) for suggestion in result.suggestions
            ],
        )


def _fallback_suggestions(request: BulletRewriteInput) -> list[BulletRewriteSuggestion]:
    examples_by_skill = _examples_by_skill(request.retrieved_examples)
    suggestions: list[BulletRewriteSuggestion] = []
    for skill in sorted({normalize_skill(skill) for skill in request.missing_skills}):
        examples = examples_by_skill.get(skill, [])
        if not examples:
            continue

        example = examples[0]
        is_grounded = _is_grounded_in_resume(skill, request.original_resume_text)
        original_bullet = _find_original_bullet(request.original_resume_text, skill)
        suggestions.append(
            BulletRewriteSuggestion(
                original_bullet=original_bullet,
                rewritten_bullet=_fallback_bullet(skill, example.example_bullet, is_grounded),
                referenced_skills=[skill],
                retrieved_example_bullets=[example.example_bullet],
                is_conditional=not is_grounded,
                grounding=_fallback_grounding(skill, is_grounded),
            )
        )
    return suggestions


def _sanitize_suggestion(
    suggestion: BulletRewriteSuggestion,
    request: BulletRewriteInput,
) -> BulletRewriteSuggestion:
    allowed_skills = {normalize_skill(skill) for skill in request.missing_skills}
    referenced_skills = [
        skill
        for skill in (normalize_skill(skill) for skill in suggestion.referenced_skills)
        if skill in allowed_skills
    ]
    allowed_bullets = {example.example_bullet for example in request.retrieved_examples}
    retrieved_example_bullets = [
        bullet for bullet in suggestion.retrieved_example_bullets if bullet in allowed_bullets
    ]
    is_grounded = all(
        _is_grounded_in_resume(skill, request.original_resume_text) for skill in referenced_skills
    )
    is_conditional = suggestion.is_conditional or not is_grounded

    grounding = suggestion.grounding
    if is_conditional and "conditional" not in grounding.lower():
        grounding = f"Conditional: {grounding}"
    rewritten_bullet = suggestion.rewritten_bullet
    if is_conditional and "conditional" not in rewritten_bullet.lower():
        rewritten_bullet = f"Conditional draft: {rewritten_bullet}"

    return BulletRewriteSuggestion(
        original_bullet=suggestion.original_bullet,
        rewritten_bullet=rewritten_bullet,
        referenced_skills=referenced_skills,
        retrieved_example_bullets=retrieved_example_bullets,
        is_conditional=is_conditional,
        grounding=grounding,
    )


def _examples_by_skill(
    examples: list[RetrievedExample],
) -> dict[str, list[RetrievedExample]]:
    grouped: dict[str, list[RetrievedExample]] = {}
    for example in examples:
        grouped.setdefault(normalize_skill(example.skill), []).append(example)
    return grouped


def _is_grounded_in_resume(skill: str, resume_text: str) -> bool:
    return normalize_skill(skill) in normalize_skill(resume_text)


def _find_original_bullet(resume_text: str, skill: str) -> str | None:
    normalized_skill = normalize_skill(skill)
    for line in resume_text.splitlines():
        cleaned = line.strip(" -*\t")
        if cleaned and normalized_skill in normalize_skill(cleaned):
            return cleaned
    return None


def _fallback_bullet(skill: str, example_bullet: str, is_grounded: bool) -> str:
    if is_grounded:
        return f"Draft rewrite using verified {skill} context: {example_bullet}"
    return (
        f"Conditional draft: adapt this structure only if you have real {skill} "
        f"experience: {example_bullet}"
    )


def _fallback_grounding(skill: str, is_grounded: bool) -> str:
    if is_grounded:
        return f"Skill '{skill}' appears in the original resume text; example supplies structure."
    return f"Uses retrieved example for {skill}; requires resume evidence before use."


def _system_prompt() -> str:
    return (
        "You rewrite resume bullet points using only the provided resume text, vacancy "
        "requirements, missing skills, and retrieved examples. Never invent experience. "
        "If a suggested skill or impact is not directly grounded in the original resume text, "
        "mark the suggestion as conditional. Return only JSON with a suggestions array."
    )


def _user_prompt(request: BulletRewriteInput) -> str:
    payload = {
        "original_resume_text": request.original_resume_text,
        "vacancy_requirements": request.vacancy_requirements.model_dump(),
        "missing_skills": request.missing_skills,
        "retrieved_examples": [example.model_dump() for example in request.retrieved_examples],
        "output_schema": {
            "suggestions": [
                {
                    "original_bullet": "string or null",
                    "rewritten_bullet": "string",
                    "referenced_skills": ["skill from missing_skills only"],
                    "retrieved_example_bullets": ["example bullet from retrieved_examples only"],
                    "is_conditional": "boolean",
                    "grounding": "string",
                }
            ]
        },
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)
