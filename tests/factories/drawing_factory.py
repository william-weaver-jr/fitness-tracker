"""Factory for Drawing entities."""

from __future__ import annotations

import datetime
import random
import uuid
from typing import Any

from fittrack.domain.enums import DrawingStatus, DrawingType
from tests.factories.base import get_faker


def make_drawing(**overrides: Any) -> dict[str, Any]:
    fake = get_faker()
    drawing_type = random.choice(list(DrawingType))
    drawing_time = fake.date_time_between(start_date="-7d", end_date="+30d")
    sales_close = drawing_time - datetime.timedelta(hours=1)

    data: dict[str, Any] = {
        "drawing_id": str(uuid.uuid4()),
        "drawing_type": drawing_type.value,
        "name": f"{drawing_type.value.capitalize()} Drawing {fake.date_this_month()}",
        "description": fake.sentence(),
        "ticket_cost_points": random.choice([50, 100, 200, 500]),
        "drawing_time": drawing_time.isoformat(),
        "ticket_sales_close": sales_close.isoformat(),
        "status": DrawingStatus.OPEN.value,
        "total_tickets": random.randint(0, 500),
    }
    data.update(overrides)
    return data
