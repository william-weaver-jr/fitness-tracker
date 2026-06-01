"""Age and age-bracket helpers."""

from __future__ import annotations

import datetime
from enum import StrEnum


class AgeBracket(StrEnum):
    B18_29 = "18-29"
    B30_39 = "30-39"
    B40_49 = "40-49"
    B50_59 = "50-59"
    B60_PLUS = "60+"


def age_from_dob(
    dob: datetime.date,
    reference: datetime.date | None = None,
) -> int:
    """Return age in whole years as of *reference* (defaults to today)."""
    today = reference or datetime.date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


def bracket_from_age(age: int) -> AgeBracket:
    """Map an age (in years) to its competition bracket.

    Raises ValueError for ages below 18 (ineligible per MVP rules).
    """
    if age < 18:
        raise ValueError(f"Age must be ≥ 18; got {age}")
    if age < 30:
        return AgeBracket.B18_29
    if age < 40:
        return AgeBracket.B30_39
    if age < 50:
        return AgeBracket.B40_49
    if age < 60:
        return AgeBracket.B50_59
    return AgeBracket.B60_PLUS
