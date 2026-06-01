"""Factory for Activity entities."""

from __future__ import annotations

import datetime
import random
import uuid
from typing import Any

from fittrack.domain.enums import ActivityType, Intensity
from tests.factories.base import get_faker


def make_activity(user_id: str | None = None, **overrides: Any) -> dict[str, Any]:
    fake = get_faker()
    start = fake.date_time_between(start_date="-60d", end_date="now")
    duration = random.randint(15, 90)
    end = start + datetime.timedelta(minutes=duration)

    data: dict[str, Any] = {
        "activity_id": str(uuid.uuid4()),
        "user_id": user_id or str(uuid.uuid4()),
        "activity_type": random.choice(list(ActivityType)).value,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "duration_minutes": duration,
        "intensity": random.choice(list(Intensity)).value,
        "points_earned": random.randint(10, 200),
        "processed": 1,
        "metrics": {
            "heartRateAvg": random.randint(100, 170),
            "steps": random.randint(0, 8000),
        },
    }
    data.update(overrides)
    return data
