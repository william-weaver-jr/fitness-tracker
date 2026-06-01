"""Base factory configuration with deterministic Faker seed."""

from __future__ import annotations

from faker import Faker

# Deterministic seed for reproducible test data across runs.
FAKER_SEED = 42

_faker = Faker()
_faker.seed_instance(FAKER_SEED)


def get_faker() -> Faker:
    return _faker
