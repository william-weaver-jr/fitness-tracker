"""Unit tests for the forward-only migration runner."""

from __future__ import annotations

import pytest

from fittrack.database.migrations import Migration, parse_migration_filename


@pytest.mark.unit
class TestParseMigrationFilename:
    def test_parses_standard_name(self) -> None:
        m = parse_migration_filename("0001_core.sql")
        assert m.version == 1
        assert m.name == "core"
        assert m.filename == "0001_core.sql"

    def test_parses_multiword_name(self) -> None:
        m = parse_migration_filename("0003_audit_tables.sql")
        assert m.version == 3
        assert m.name == "audit_tables"

    def test_parses_high_version(self) -> None:
        m = parse_migration_filename("0099_last_migration.sql")
        assert m.version == 99

    def test_invalid_filename_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_migration_filename("not_a_migration.sql")

        with pytest.raises(ValueError):
            parse_migration_filename("core.sql")

    def test_non_sql_extension_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_migration_filename("0001_core.txt")


@pytest.mark.unit
class TestMigrationOrdering:
    def test_migrations_sort_by_version(self) -> None:
        m1 = parse_migration_filename("0003_audit.sql")
        m2 = parse_migration_filename("0001_core.sql")
        m3 = parse_migration_filename("0002_views.sql")

        ordered = sorted([m1, m2, m3])
        assert [m.version for m in ordered] == [1, 2, 3]

    def test_migrations_compare_equal_by_version(self) -> None:
        m1 = parse_migration_filename("0001_core.sql")
        m2 = parse_migration_filename("0001_core.sql")
        assert m1 == m2


@pytest.mark.unit
class TestMigrationDataclass:
    def test_migration_has_expected_fields(self) -> None:
        m = Migration(version=1, name="core", filename="0001_core.sql")
        assert m.version == 1
        assert m.name == "core"
        assert m.filename == "0001_core.sql"
