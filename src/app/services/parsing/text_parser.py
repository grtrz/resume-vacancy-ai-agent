import codecs
import logging

from app.services.parsing.base import BaseParser, ParsingError
from app.services.parsing.text_cleaner import clean_text

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """Parser for plain text files."""

    _FALLBACK_ENCODINGS = ("utf-8-sig", "cp1252")

    def parse(self, content: bytes) -> str:
        if not content:
            raise ParsingError("Text content is empty")

        try:
            text = self._decode(content)
        except UnicodeDecodeError as exc:
            logger.exception("Failed to decode text content")
            raise ParsingError("Failed to decode text content") from exc

        return clean_text(text)

    def _decode(self, content: bytes) -> str:
        if content.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            return content.decode("utf-16")

        last_error: UnicodeDecodeError | None = None

        for encoding in self._FALLBACK_ENCODINGS:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError as exc:
                last_error = exc

        if last_error is None:
            msg = "No text encodings configured"
            raise RuntimeError(msg)
        raise last_error
