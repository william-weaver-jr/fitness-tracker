"""Tier code computation.

Tier codes are derived — never stored as source of truth. Always recompute
from (sex, age_bracket, fitness_level) via compute_tier_code().
"""

from __future__ import annotations

from typing import NamedTuple

from fittrack.domain.age import AgeBracket
from fittrack.domain.enums import FitnessLevel, Sex

# Regex pattern for a valid tier code.
TIER_CODE_PATTERN = r"^(M|F)-(18-29|30-39|40-49|50-59|60\+)-(BEG|INT|ADV)$"


def compute_tier_code(sex: Sex, bracket: AgeBracket, level: FitnessLevel) -> str:
    """Return the canonical tier code string, e.g. 'M-30-39-INT'."""
    return f"{sex.tier_code_letter}-{bracket.value}-{level.tier_code_abbr}"


class TierCode(NamedTuple):
    """Parsed representation of a tier code string."""

    sex: Sex
    bracket: AgeBracket
    level: FitnessLevel

    @property
    def code(self) -> str:
        return compute_tier_code(self.sex, self.bracket, self.level)

    @classmethod
    def parse(cls, code: str) -> TierCode:
        """Parse a tier code string into its components.

        Raises ValueError if the format is invalid.
        """
        import re

        if not re.match(TIER_CODE_PATTERN, code):
            raise ValueError(f"Invalid tier code: '{code}'")

        parts = code.split("-", 1)  # ['M', '18-29-BEG'] or ['F', '60+-ADV']
        sex_letter = parts[0]
        rest = parts[1]  # e.g. '30-39-INT' or '60+-ADV'

        sex = Sex.MALE if sex_letter == "M" else Sex.FEMALE

        # Split off the level suffix (last 3-4 chars after last '-')
        last_dash = rest.rfind("-")
        bracket_str = rest[:last_dash]
        level_abbr = rest[last_dash + 1 :]

        bracket = AgeBracket(bracket_str)

        abbr_to_level = {
            "BEG": FitnessLevel.BEGINNER,
            "INT": FitnessLevel.INTERMEDIATE,
            "ADV": FitnessLevel.ADVANCED,
        }
        level = abbr_to_level[level_abbr]

        return cls(sex=sex, bracket=bracket, level=level)
