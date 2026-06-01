"""Unit tests for domain enums."""

from __future__ import annotations

import pytest

from fittrack.domain.enums import (
    ActivityType,
    DrawingStatus,
    DrawingType,
    FitnessLevel,
    FulfillmentStatus,
    Intensity,
    Provider,
    Role,
    Sex,
    UserStatus,
)


@pytest.mark.unit
class TestUserStatus:
    def test_values(self) -> None:
        assert UserStatus.PENDING.value == "pending"
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.SUSPENDED.value == "suspended"
        assert UserStatus.DEACTIVATED.value == "deactivated"

    def test_all_statuses(self) -> None:
        values = {s.value for s in UserStatus}
        assert values == {"pending", "active", "suspended", "deactivated"}


@pytest.mark.unit
class TestRole:
    def test_values(self) -> None:
        assert Role.USER.value == "user"
        assert Role.PREMIUM.value == "premium"
        assert Role.ADMIN.value == "admin"

    def test_all_roles(self) -> None:
        values = {r.value for r in Role}
        assert values == {"user", "premium", "admin"}


@pytest.mark.unit
class TestSex:
    def test_values(self) -> None:
        assert Sex.MALE.value == "male"
        assert Sex.FEMALE.value == "female"

    def test_tier_code_letter(self) -> None:
        assert Sex.MALE.tier_code_letter == "M"
        assert Sex.FEMALE.tier_code_letter == "F"


@pytest.mark.unit
class TestFitnessLevel:
    def test_values(self) -> None:
        assert FitnessLevel.BEGINNER.value == "beginner"
        assert FitnessLevel.INTERMEDIATE.value == "intermediate"
        assert FitnessLevel.ADVANCED.value == "advanced"

    def test_tier_code_abbrs(self) -> None:
        assert FitnessLevel.BEGINNER.tier_code_abbr == "BEG"
        assert FitnessLevel.INTERMEDIATE.tier_code_abbr == "INT"
        assert FitnessLevel.ADVANCED.tier_code_abbr == "ADV"

    def test_three_levels(self) -> None:
        assert len(FitnessLevel) == 3


@pytest.mark.unit
class TestProvider:
    def test_values(self) -> None:
        assert Provider.APPLE_HEALTH.value == "apple_health"
        assert Provider.GOOGLE_FIT.value == "google_fit"
        assert Provider.FITBIT.value == "fitbit"

    def test_all_providers(self) -> None:
        values = {p.value for p in Provider}
        assert values == {"apple_health", "google_fit", "fitbit"}


@pytest.mark.unit
class TestActivityType:
    def test_core_types_exist(self) -> None:
        assert ActivityType.RUNNING.value == "running"
        assert ActivityType.WALKING.value == "walking"
        assert ActivityType.CYCLING.value == "cycling"
        assert ActivityType.SWIMMING.value == "swimming"
        assert ActivityType.STRENGTH_TRAINING.value == "strength_training"
        assert ActivityType.YOGA.value == "yoga"
        assert ActivityType.HIIT.value == "hiit"
        assert ActivityType.OTHER.value == "other"


@pytest.mark.unit
class TestIntensity:
    def test_values(self) -> None:
        assert Intensity.LOW.value == "low"
        assert Intensity.MODERATE.value == "moderate"
        assert Intensity.HIGH.value == "high"
        assert Intensity.VERY_HIGH.value == "very_high"

    def test_all_intensities(self) -> None:
        values = {i.value for i in Intensity}
        assert values == {"low", "moderate", "high", "very_high"}


@pytest.mark.unit
class TestDrawingType:
    def test_values(self) -> None:
        assert DrawingType.DAILY.value == "daily"
        assert DrawingType.WEEKLY.value == "weekly"
        assert DrawingType.MONTHLY.value == "monthly"
        assert DrawingType.ANNUAL.value == "annual"

    def test_all_types(self) -> None:
        values = {d.value for d in DrawingType}
        assert values == {"daily", "weekly", "monthly", "annual"}


@pytest.mark.unit
class TestDrawingStatus:
    def test_values(self) -> None:
        assert DrawingStatus.DRAFT.value == "draft"
        assert DrawingStatus.SCHEDULED.value == "scheduled"
        assert DrawingStatus.OPEN.value == "open"
        assert DrawingStatus.CLOSED.value == "closed"
        assert DrawingStatus.COMPLETED.value == "completed"
        assert DrawingStatus.CANCELLED.value == "cancelled"

    def test_all_statuses(self) -> None:
        values = {d.value for d in DrawingStatus}
        assert values == {"draft", "scheduled", "open", "closed", "completed", "cancelled"}


@pytest.mark.unit
class TestFulfillmentStatus:
    def test_values(self) -> None:
        assert FulfillmentStatus.PENDING.value == "pending"
        assert FulfillmentStatus.NOTIFIED.value == "notified"
        assert FulfillmentStatus.ADDRESS_CONFIRMED.value == "address_confirmed"
        assert FulfillmentStatus.SHIPPED.value == "shipped"
        assert FulfillmentStatus.DELIVERED.value == "delivered"
        assert FulfillmentStatus.FORFEITED.value == "forfeited"

    def test_all_statuses(self) -> None:
        values = {f.value for f in FulfillmentStatus}
        assert values == {
            "pending",
            "notified",
            "address_confirmed",
            "shipped",
            "delivered",
            "forfeited",
        }
