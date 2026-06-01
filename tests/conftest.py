"""Shared pytest fixtures.

Note: integration-test fixtures (Oracle connection, migrated schema, seeded data)
are intentionally not defined yet — they land with Task #8 (DB layer).
"""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-mark tests by directory.

    - `tests/unit/**`        → @pytest.mark.unit
    - `tests/integration/**` → @pytest.mark.integration
    """
    for item in items:
        path = str(item.fspath)
        if "/tests/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
