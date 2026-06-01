"""Domain enums for FitTrack."""

from __future__ import annotations

from enum import StrEnum


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class Role(StrEnum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"

    @property
    def tier_code_letter(self) -> str:
        return "M" if self == Sex.MALE else "F"


class FitnessLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    @property
    def tier_code_abbr(self) -> str:
        return {"beginner": "BEG", "intermediate": "INT", "advanced": "ADV"}[self.value]


class Provider(StrEnum):
    APPLE_HEALTH = "apple_health"
    GOOGLE_FIT = "google_fit"
    FITBIT = "fitbit"


class ActivityType(StrEnum):
    RUNNING = "running"
    WALKING = "walking"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    STRENGTH_TRAINING = "strength_training"
    YOGA = "yoga"
    HIIT = "hiit"
    OTHER = "other"


class Intensity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DrawingType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class DrawingStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    OPEN = "open"
    CLOSED = "closed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FulfillmentStatus(StrEnum):
    PENDING = "pending"
    NOTIFIED = "notified"
    ADDRESS_CONFIRMED = "address_confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    FORFEITED = "forfeited"


class PointTransactionType(StrEnum):
    EARN = "earn"
    SPEND = "spend"
    ADJUST = "adjust"
    EXPIRE = "expire"
