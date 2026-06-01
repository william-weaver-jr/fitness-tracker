"""Unit tests for entity factories."""

from __future__ import annotations

import pytest

from tests.factories.activity_factory import make_activity
from tests.factories.drawing_factory import make_drawing
from tests.factories.profile_factory import make_profile
from tests.factories.sponsor_factory import make_sponsor
from tests.factories.user_factory import make_admin_user, make_premium_user, make_user


@pytest.mark.unit
class TestUserFactory:
    def test_make_user_returns_dict_with_required_fields(self) -> None:
        user = make_user()
        assert "user_id" in user
        assert "email" in user
        assert "status" in user
        assert "role" in user
        assert user["role"] == "user"

    def test_make_admin_user(self) -> None:
        user = make_admin_user()
        assert user["role"] == "admin"

    def test_make_premium_user(self) -> None:
        user = make_premium_user()
        assert user["role"] == "premium"

    def test_overrides_applied(self) -> None:
        user = make_user(email="custom@example.com", point_balance=9999)
        assert user["email"] == "custom@example.com"
        assert user["point_balance"] == 9999

    def test_unique_emails(self) -> None:
        emails = {make_user()["email"] for _ in range(10)}
        assert len(emails) == 10


@pytest.mark.unit
class TestProfileFactory:
    def test_make_profile_has_tier_code(self) -> None:
        profile = make_profile()
        assert "tier_code" in profile
        assert profile["tier_code"]

    def test_tier_code_format(self) -> None:
        import re

        from fittrack.domain.tier import TIER_CODE_PATTERN

        profile = make_profile()
        assert re.match(TIER_CODE_PATTERN, profile["tier_code"])

    def test_state_is_eligible(self) -> None:
        from fittrack.domain.states import is_eligible_state

        for _ in range(20):
            profile = make_profile()
            assert is_eligible_state(profile["state_of_residence"])

    def test_user_id_override(self) -> None:
        profile = make_profile(user_id="abc-123")
        assert profile["user_id"] == "abc-123"

    def test_age_18_or_older(self) -> None:
        import datetime

        for _ in range(20):
            profile = make_profile()
            dob = datetime.date.fromisoformat(profile["date_of_birth"])
            age = (datetime.date.today() - dob).days // 365
            assert age >= 18


@pytest.mark.unit
class TestActivityFactory:
    def test_make_activity_has_required_fields(self) -> None:
        activity = make_activity()
        assert "activity_id" in activity
        assert "activity_type" in activity
        assert "start_time" in activity
        assert "duration_minutes" in activity

    def test_points_earned_positive(self) -> None:
        for _ in range(10):
            assert make_activity()["points_earned"] > 0

    def test_user_id_override(self) -> None:
        uid = "user-abc"
        activity = make_activity(user_id=uid)
        assert activity["user_id"] == uid


@pytest.mark.unit
class TestDrawingFactory:
    def test_make_drawing_has_required_fields(self) -> None:
        drawing = make_drawing()
        assert "drawing_id" in drawing
        assert "drawing_type" in drawing
        assert "ticket_cost_points" in drawing
        assert drawing["ticket_cost_points"] > 0

    def test_sales_close_before_drawing_time(self) -> None:
        import datetime

        drawing = make_drawing()
        close = datetime.datetime.fromisoformat(drawing["ticket_sales_close"])
        draw = datetime.datetime.fromisoformat(drawing["drawing_time"])
        assert close < draw


@pytest.mark.unit
class TestSponsorFactory:
    def test_make_sponsor_has_required_fields(self) -> None:
        sponsor = make_sponsor()
        assert "sponsor_id" in sponsor
        assert "name" in sponsor
        assert sponsor["status"] == "active"
