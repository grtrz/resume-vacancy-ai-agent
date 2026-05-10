from app.schemas.extraction import ExtractedProfile


class LlmExtractor:
    def extract_resume(self, text: str) -> ExtractedProfile:
        _ = text
        return ExtractedProfile()
