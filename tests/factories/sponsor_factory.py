"""Factory for Sponsor entities."""

from __future__ import annotations

import uuid
from typing import Any

from tests.factories.base import get_faker


def make_sponsor(**overrides: Any) -> dict[str, Any]:
    fake = get_faker()
    data: dict[str, Any] = {
        "sponsor_id": str(uuid.uuid4()),
        "name": fake.company(),
        "contact_name": fake.name(),
        "contact_email": fake.company_email(),
        "contact_phone": fake.phone_number(),
        "website_url": fake.url(),
        "logo_url": f"https://cdn.fittrack.example/sponsors/{uuid.uuid4()}.png",
        "status": "active",
    }
    data.update(overrides)
    return data
