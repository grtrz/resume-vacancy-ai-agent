from abc import ABC, abstractmethod

from app.core.exceptions import ResumeVacancyAgentError


class ParsingError(ResumeVacancyAgentError):
    """Raised when document text extraction fails."""


class BaseParser(ABC):
    """Interface for document parsers."""

    @abstractmethod
    def parse(self, content: bytes) -> str:
        """Extract clean text from document bytes."""
