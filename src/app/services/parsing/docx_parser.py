import logging
from collections.abc import Iterator
from io import BytesIO

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from app.services.parsing.base import BaseParser, ParsingError
from app.services.parsing.text_cleaner import clean_text

logger = logging.getLogger(__name__)


class DocxParser(BaseParser):
    def parse(self, content: bytes) -> str:
        if not content:
            raise ParsingError("DOCX content is empty")

        try:
            document = Document(BytesIO(content))
            blocks = list(_extract_blocks(document))
        except Exception as exc:
            logger.exception("Failed to parse DOCX content")
            raise ParsingError("Failed to parse DOCX content") from exc

        text = clean_text("\n".join(blocks))
        if not text:
            logger.warning("DOCX parsing completed without extracting text")
        return text


def _extract_blocks(document: DocumentObject) -> Iterator[str]:
    for block in _iter_block_items(document):
        if isinstance(block, Paragraph):
            text = _paragraph_text(block)
            if text:
                yield text
        else:
            yield from _table_rows(block)


def _iter_block_items(parent: DocumentObject | _Cell) -> Iterator[Paragraph | Table]:
    parent_element = parent.element.body if isinstance(parent, DocumentObject) else parent._tc

    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _paragraph_text(paragraph: Paragraph) -> str:
    text = paragraph.text.strip()
    if not text:
        return ""

    style_name = paragraph.style.name.lower() if paragraph.style else ""
    if "bullet" in style_name and not text.startswith(("-", "*")):
        return f"- {text}"
    return text


def _table_rows(table: Table) -> Iterator[str]:
    for row in table.rows:
        cells = [clean_text(cell.text).replace("\n", " ") for cell in row.cells]
        text = " | ".join(cell for cell in cells if cell)
        if text:
            yield text
