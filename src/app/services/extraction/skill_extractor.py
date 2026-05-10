from app.schemas.extraction import ExtractedProfile
from app.services.extraction.normalizer import normalize_token


class SkillExtractor:
    def extract(self, text: str) -> ExtractedProfile:
        tokens = {normalize_token(token) for token in text.replace(",", " ").split()}
        skills = sorted(token for token in tokens if token in {"python", "fastapi", "sql"})
        return ExtractedProfile(hard_skills=skills)
