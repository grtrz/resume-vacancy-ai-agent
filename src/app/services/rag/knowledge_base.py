from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[4] / "data" / "knowledge_base"


class KnowledgeBaseExample(BaseModel):
    model_config = ConfigDict(frozen=True)

    skill: str = Field(min_length=1)
    category: str = Field(min_length=1)
    example_bullet: str = Field(min_length=1)

    @field_validator("skill", "category", "example_bullet")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return " ".join(value.strip().split())

    def searchable_text(self) -> str:
        return f"{self.skill}\n{self.category}\n{self.example_bullet}"


class KnowledgeBase:
    def __init__(self, path: Path | str = DEFAULT_KNOWLEDGE_BASE_DIR) -> None:
        self._path = Path(path)

    @cached_property
    def examples(self) -> tuple[KnowledgeBaseExample, ...]:
        return tuple(_deduplicate(self._load_examples()))

    def _load_examples(self) -> list[KnowledgeBaseExample]:
        if not self._path.exists():
            return []

        examples: list[KnowledgeBaseExample] = []
        for path in sorted(self._path.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() == ".json":
                examples.extend(_load_json_examples(path))
            elif path.suffix.lower() == ".txt":
                examples.extend(_load_txt_examples(path))
        return examples


def _load_json_examples(path: Path) -> list[KnowledgeBaseExample]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = _json_items(payload)
    return [KnowledgeBaseExample.model_validate(item) for item in items]


def _json_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [_normalize_item_keys(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        examples = payload.get("examples")
        if isinstance(examples, list):
            return [_normalize_item_keys(item) for item in examples if isinstance(item, dict)]
        return [_normalize_item_keys(payload)]
    return []


def _load_txt_examples(path: Path) -> list[KnowledgeBaseExample]:
    examples: list[KnowledgeBaseExample] = []
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                continue
            normalized_key = key.strip().lower().replace(" ", "_")
            model_key = _model_key(normalized_key)
            if model_key is not None:
                fields[model_key] = value.strip()
        if fields:
            examples.append(KnowledgeBaseExample.model_validate(fields))
    return examples


def _deduplicate(
    examples: list[KnowledgeBaseExample],
) -> list[KnowledgeBaseExample]:
    deduplicated: dict[tuple[str, str, str], KnowledgeBaseExample] = {}
    for example in examples:
        key = (
            example.skill.lower(),
            example.category.lower(),
            example.example_bullet.lower(),
        )
        deduplicated.setdefault(key, example)
    return list(deduplicated.values())


def _normalize_item_keys(item: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in item.items():
        model_key = _model_key(key.strip().lower().replace(" ", "_"))
        normalized[model_key or key] = value
    return normalized


def _model_key(key: str) -> str | None:
    if key in {"skill", "category", "example_bullet"}:
        return key
    if key in {"bullet", "bullet_point", "example_bullet_point"}:
        return "example_bullet"
    return None
