"""Factory for Profile entities."""

from __future__ import annotations

import datetime
import random
import uuid
from typing import Any

from fittrack.domain.age import bracket_from_age
from fittrack.domain.enums import FitnessLevel, Sex
from fittrack.domain.states import ELIGIBLE_STATES
from fittrack.domain.tier import compute_tier_code
from tests.factories.base import get_faker

_ELIGIBLE_STATES_LIST = sorted(ELIGIBLE_STATES)


def make_profile(user_id: str | None = None, **overrides: Any) -> dict[str, Any]:
    fake = get_faker()
    age = fake.random_int(min=18, max=80)
    dob = datetime.date.today() - datetime.timedelta(days=age * 365)
    sex = random.choice(list(Sex))
    bracket = bracket_from_age(age)
    level = random.choice(list(FitnessLevel))

    data: dict[str, Any] = {
        "profile_id": str(uuid.uuid4()),
        "user_id": user_id or str(uuid.uuid4()),
        "display_name": fake.user_name(),
        "date_of_birth": dob.isoformat(),
        "state_of_residence": random.choice(_ELIGIBLE_STATES_LIST),
        "biological_sex": sex.value,
        "age_bracket": bracket.value,
        "fitness_level": level.value,
        "tier_code": compute_tier_code(sex, bracket, level),
        "height_inches": fake.random_int(min=58, max=78),
        "weight_pounds": fake.random_int(min=100, max=280),
    }
    data.update(overrides)
    return data
