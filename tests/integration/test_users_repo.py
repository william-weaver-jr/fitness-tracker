"""Integration tests: users repository against live Oracle Free container."""

from __future__ import annotations

from typing import Any

import pytest

from fittrack.database.repositories import users_repo


async def _insert_user(conn: Any, *, email: str = "test@example.com") -> str:
    """Insert a minimal user row; return the RAWTOHEX user_id."""
    cursor = await conn.cursor()
    await cursor.execute(
        "INSERT INTO users (email, password_hash, status, email_verified) "
        "VALUES (:1, :2, 'active', 1)",
        [email, "hashed_pw"],
    )
    await conn.commit()
    await cursor.execute("SELECT RAWTOHEX(user_id) FROM users WHERE email = :1", [email])
    row = await cursor.fetchone()
    assert row is not None
    return str(row[0])


@pytest.mark.integration
async def test_list_users_empty_on_clean_db(clean_db: Any) -> None:
    items, total = await users_repo.list_users()
    assert total == 0
    assert items == []


@pytest.mark.integration
async def test_list_users_reflects_insert(clean_db: Any) -> None:
    await _insert_user(clean_db, email="alice@example.com")
    items, total = await users_repo.list_users()
    assert total == 1
    assert items[0]["email"] == "alice@example.com"


@pytest.mark.integration
async def test_get_user_returns_expected_fields(clean_db: Any) -> None:
    uid = await _insert_user(clean_db, email="bob@example.com")
    user = await users_repo.get_user(uid)
    assert user is not None
    assert user["email"] == "bob@example.com"
    assert user["status"] == "active"
    assert "pointBalance" in user
    assert "version" in user
    assert "createdAt" in user


@pytest.mark.integration
async def test_get_user_not_found_returns_none(clean_db: Any) -> None:
    result = await users_repo.get_user("A" * 32)
    assert result is None


@pytest.mark.integration
async def test_delete_user_returns_true(clean_db: Any) -> None:
    uid = await _insert_user(clean_db, email="carol@example.com")
    assert await users_repo.delete_user(uid) is True


@pytest.mark.integration
async def test_delete_user_removes_row(clean_db: Any) -> None:
    uid = await _insert_user(clean_db, email="dave@example.com")
    await users_repo.delete_user(uid)
    assert await users_repo.get_user(uid) is None


@pytest.mark.integration
async def test_delete_nonexistent_user_returns_false(clean_db: Any) -> None:
    assert await users_repo.delete_user("B" * 32) is False


@pytest.mark.integration
async def test_list_users_pagination(clean_db: Any) -> None:
    for i in range(5):
        await _insert_user(clean_db, email=f"page_user{i}@example.com")
    items, total = await users_repo.list_users(limit=2, offset=0)
    assert total == 5
    assert len(items) == 2


@pytest.mark.integration
async def test_list_users_pagination_offset(clean_db: Any) -> None:
    for i in range(4):
        await _insert_user(clean_db, email=f"offset_user{i}@example.com")
    page1, _ = await users_repo.list_users(limit=2, offset=0)
    page2, _ = await users_repo.list_users(limit=2, offset=2)
    all_emails = {u["email"] for u in page1 + page2}
    assert len(all_emails) == 4
