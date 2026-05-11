import logging

import fitz

from app.services.parsing.base import BaseParser, ParsingError
from app.services.parsing.text_cleaner import clean_text

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    def parse(self, content: bytes) -> str:
        if not content:
            raise ParsingError("PDF content is empty")

        try:
            with fitz.open(stream=content, filetype="pdf") as document:
                if document.needs_pass:
                    raise ParsingError("Encrypted PDFs are not supported")

                pages: list[str] = []
                for page in document:
                    page_text = page.get_text("text", sort=True).strip()
                    if page_text:
                        pages.append(page_text)
        except ParsingError:
            raise
        except Exception as exc:
            logger.exception("Failed to parse PDF content")
            raise ParsingError("Failed to parse PDF content") from exc

        text = clean_text("\n\n".join(pages))
        if not text:
            logger.warning("PDF parsing completed without extracting text")
        return text
