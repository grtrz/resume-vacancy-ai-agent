import re
import unicodedata

_INLINE_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
_BULLET_PREFIX_RE = re.compile(r"^([-*])\s*")
_BULLET_LINE_RE = re.compile(r"^(?:[-*]|\d+[.)])\s+\S")
_TRANSLATION_TABLE = str.maketrans(
    {
        "\u00a0": " ",
        "\u1680": " ",
        "\u180e": "",
        "\u2000": " ",
        "\u2001": " ",
        "\u2002": " ",
        "\u2003": " ",
        "\u2004": " ",
        "\u2005": " ",
        "\u2006": " ",
        "\u2007": " ",
        "\u2008": " ",
        "\u2009": " ",
        "\u200a": " ",
        "\u200b": "",
        "\u200c": "",
        "\u200d": "",
        "\u2022": "-",
        "\u2023": "-",
        "\u2043": "-",
        "\u2219": "-",
        "\uf0b7": "-",
        "\ufeff": "",
    }
)


def clean_text(text: str) -> str:
    """Normalize extracted text while preserving meaningful line breaks."""
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.translate(_TRANSLATION_TABLE)

    lines = [_clean_line(line) for line in normalized.split("\n")]
    return "\n".join(_collapse_blank_lines(lines)).strip()


def _clean_line(line: str) -> str:
    line = _INLINE_WHITESPACE_RE.sub(" ", line).strip()
    return _BULLET_PREFIX_RE.sub(r"\1 ", line)


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    cleaned_lines: list[str] = []

    for index, line in enumerate(lines):
        if not line:
            next_line = _next_non_empty_line(lines, index)
            if (
                cleaned_lines
                and cleaned_lines[-1]
                and next_line
                and _is_bullet_line(cleaned_lines[-1])
                and _is_bullet_line(next_line)
            ):
                continue
            if cleaned_lines and cleaned_lines[-1]:
                cleaned_lines.append("")
            continue
        cleaned_lines.append(line)

    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()

    return cleaned_lines


def _next_non_empty_line(lines: list[str], start_index: int) -> str | None:
    for line in lines[start_index + 1 :]:
        if line:
            return line
    return None


def _is_bullet_line(line: str) -> bool:
    return bool(_BULLET_LINE_RE.match(line))
