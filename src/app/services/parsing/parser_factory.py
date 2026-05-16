from pathlib import PurePath

from app.services.parsing.base import BaseParser
from app.services.parsing.docx_parser import DocxParser
from app.services.parsing.pdf_parser import PdfParser
from app.services.parsing.text_parser import TextParser

_PARSER_BY_EXTENSION: dict[str, type[BaseParser]] = {
    ".docx": DocxParser,
    ".pdf": PdfParser,
    ".txt": TextParser,
}

_PARSER_BY_CONTENT_TYPE: dict[str, type[BaseParser]] = {
    "application/pdf": PdfParser,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
    "text/plain": TextParser,
}


def parser_for_upload(filename: str | None, content_type: str | None) -> BaseParser | None:
    parser_type = _parser_type_from_filename(filename) or _parser_type_from_content_type(
        content_type
    )
    if parser_type is None:
        return None
    return parser_type()


def _parser_type_from_filename(filename: str | None) -> type[BaseParser] | None:
    if not filename:
        return None
    suffix = PurePath(filename).suffix.lower()
    return _PARSER_BY_EXTENSION.get(suffix)


def _parser_type_from_content_type(content_type: str | None) -> type[BaseParser] | None:
    if not content_type:
        return None
    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    return _PARSER_BY_CONTENT_TYPE.get(media_type)
