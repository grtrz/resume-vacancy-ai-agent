from __future__ import annotations

import re
from collections.abc import Iterable

from app.schemas.extraction import ExperienceRange

_YEAR_UNIT = r"(?:years?|yrs?)"
_NUMBER = r"(?P<years>\d+(?:\.\d+)?)"
_RANGE_START = r"(?P<minimum>\d+(?:\.\d+)?)"
_RANGE_END = r"(?P<maximum>\d+(?:\.\d+)?)"

_RANGE_PATTERNS = [
    re.compile(
        rf"\b{_RANGE_START}\s*(?:-|to)\s*{_RANGE_END}\s*{_YEAR_UNIT}\b",
        re.IGNORECASE,
    ),
]

_MINIMUM_PATTERNS = [
    re.compile(
        rf"\b(?:at\s+least|minimum|min\.?|from|not\s+less\s+than)\s+{_NUMBER}\s*\+?\s*{_YEAR_UNIT}\b",
        re.IGNORECASE,
    ),
    re.compile(rf"\b{_NUMBER}\s*\+\s*{_YEAR_UNIT}\b", re.IGNORECASE),
]

_YEAR_PATTERNS = [
    *_MINIMUM_PATTERNS,
    re.compile(rf"\b{_NUMBER}\s*{_YEAR_UNIT}(?:\s+of\s+experience)?\b", re.IGNORECASE),
]


def _to_float(value: str) -> float:
    return float(value)


def _iter_year_values(text: str) -> Iterable[float]:
    for pattern in _YEAR_PATTERNS:
        for match in pattern.finditer(text):
            yield _to_float(match.group("years"))
    for pattern in _RANGE_PATTERNS:
        for match in pattern.finditer(text):
            yield _to_float(match.group("maximum"))


def extract_years_of_experience(text: str) -> float | None:
    """Return the largest explicit years-of-experience value in text."""

    years = list(_iter_year_values(text))
    if not years:
        return None
    return max(years)


def extract_experience_range(text: str) -> ExperienceRange | None:
    for pattern in _RANGE_PATTERNS:
        match = pattern.search(text)
        if match:
            minimum = _to_float(match.group("minimum"))
            maximum = _to_float(match.group("maximum"))
            return ExperienceRange(minimum_years=minimum, maximum_years=maximum)

    for pattern in _MINIMUM_PATTERNS:
        match = pattern.search(text)
        if match:
            return ExperienceRange(minimum_years=_to_float(match.group("years")))

    years = extract_years_of_experience(text)
    if years is None:
        return None
    return ExperienceRange(minimum_years=years)
