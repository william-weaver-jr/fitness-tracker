"""Shared Pydantic base config for camelCase API serialization."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _to_camel(field: str) -> str:
    """Convert snake_case to camelCase."""
    parts = field.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class ApiModel(BaseModel):
    """Base model: camelCase JSON aliases, snake_case attributes internally."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
    )
