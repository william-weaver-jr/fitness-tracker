"""Seed the development database with synthetic data.

Creates:
  - 5 admin + 5 premium + 300 regular users (10 per tier)
  - Profiles for all 310 users (covers all 30 tier combinations)
  - 5 sponsors
  - 30 drawings (mix of types and statuses)
  - 60-day activity history for ~50 users
  - ~5,000 tickets across open drawings
  - 8 prize fulfillment records in varied states

Target: completes in under 60 seconds.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running directly: python scripts/seed_data.py
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import datetime
import random
import uuid

from fittrack.domain.age import AgeBracket
from fittrack.domain.enums import (
    ActivityType,
    DrawingStatus,
    DrawingType,
    FitnessLevel,
    Intensity,
    Sex,
)
from fittrack.domain.states import ELIGIBLE_STATES
from fittrack.domain.tier import compute_tier_code

ELIGIBLE_STATES_LIST = sorted(ELIGIBLE_STATES)
SEED = 42
random.seed(SEED)

_conn: object = None  # type: ignore[assignment]


async def _exec(sql: str, params: list | None = None) -> object:
    cursor = await _conn.cursor()  # type: ignore[union-attr]
    await cursor.execute(sql, params or [])
    return cursor


async def _commit() -> None:
    await _conn.commit()  # type: ignore[union-attr]


async def seed_sponsors() -> list[str]:
    print("  Seeding sponsors...")
    names = ["FitGear Pro", "ActiveWear Co", "NutriBlend", "SportsTech Inc", "WellnessPlus"]
    ids = []
    for name in names:
        sid = str(uuid.uuid4()).replace("-", "").upper()
        await _exec(
            """
            INSERT INTO sponsors (sponsor_id, name, contact_email, website_url, status)
            VALUES (HEXTORAW(:1), :2, :3, :4, 'active')
            """,
            [sid, name, f"contact@{name.lower().replace(' ', '')}.com", f"https://{name.lower().replace(' ', '')}.com"],
        )
        ids.append(sid)
    await _commit()
    print(f"    Created {len(ids)} sponsors")
    return ids


async def seed_users_and_profiles() -> list[tuple[str, str]]:
    """Return list of (user_id, tier_code) tuples."""
    print("  Seeding users and profiles...")
    users: list[tuple[str, str]] = []

    all_tiers = [
        (sex, bracket, level)
        for sex in Sex
        for bracket in AgeBracket
        for level in FitnessLevel
    ]

    # 5 admin users
    for i in range(5):
        uid = str(uuid.uuid4()).replace("-", "").upper()
        email = f"admin{i+1}@fittrack.internal"
        await _exec(
            """
            INSERT INTO users (user_id, email, password_hash, email_verified, status, role, point_balance)
            VALUES (HEXTORAW(:1), :2, '$argon2id$v=19$admin_hash', 1, 'active', 'admin', 0)
            """,
            [uid, email],
        )
        sex, bracket, level = all_tiers[i % 30]
        tier = compute_tier_code(sex, bracket, level)
        await _insert_profile(uid, sex, bracket, level, tier, age=35 + i)
        users.append((uid, tier))

    # 5 premium users
    for i in range(5):
        uid = str(uuid.uuid4()).replace("-", "").upper()
        email = f"premium{i+1}@example.com"
        points = random.randint(500, 5000)
        await _exec(
            """
            INSERT INTO users (user_id, email, password_hash, email_verified, status, role, point_balance)
            VALUES (HEXTORAW(:1), :2, '$argon2id$v=19$premium_hash', 1, 'active', 'premium', :3)
            """,
            [uid, email, points],
        )
        sex, bracket, level = all_tiers[(i + 5) % 30]
        tier = compute_tier_code(sex, bracket, level)
        await _insert_profile(uid, sex, bracket, level, tier, age=28 + i * 2)
        users.append((uid, tier))

    # 300 regular users: 10 per tier (30 tiers)
    user_num = 1
    for sex, bracket, level in all_tiers:
        tier = compute_tier_code(sex, bracket, level)
        age_range = _bracket_age_range(bracket)
        for j in range(10):
            uid = str(uuid.uuid4()).replace("-", "").upper()
            email = f"user{user_num:04d}@example.com"
            points = random.randint(0, 3000)
            await _exec(
                """
                INSERT INTO users (user_id, email, password_hash, email_verified, status, role, point_balance)
                VALUES (HEXTORAW(:1), :2, '$argon2id$v=19$user_hash', 1, 'active', 'user', :3)
                """,
                [uid, email, points],
            )
            age = random.randint(*age_range)
            await _insert_profile(uid, sex, bracket, level, tier, age=age)
            users.append((uid, tier))
            user_num += 1

    await _commit()
    print(f"    Created {len(users)} users with profiles")
    return users


async def _insert_profile(
    user_id: str,
    sex: Sex,
    bracket: AgeBracket,
    level: FitnessLevel,
    tier: str,
    age: int,
) -> None:
    dob = datetime.date.today() - datetime.timedelta(days=age * 365 + random.randint(0, 364))
    state = random.choice(ELIGIBLE_STATES_LIST)
    height = random.randint(60, 78)
    weight = random.randint(110, 260)
    await _exec(
        """
        INSERT INTO profiles (user_id, display_name, date_of_birth, state_of_residence,
                              biological_sex, age_bracket, fitness_level, tier_code,
                              height_inches, weight_pounds)
        VALUES (HEXTORAW(:1), :2, TO_DATE(:3, 'YYYY-MM-DD'), :4, :5, :6, :7, :8, :9, :10)
        """,
        [
            user_id,
            f"user_{user_id[:8].lower()}",
            dob.isoformat(),
            state,
            sex.value,
            bracket.value,
            level.value,
            tier,
            height,
            weight,
        ],
    )


def _bracket_age_range(bracket: AgeBracket) -> tuple[int, int]:
    return {
        AgeBracket.B18_29: (18, 29),
        AgeBracket.B30_39: (30, 39),
        AgeBracket.B40_49: (40, 49),
        AgeBracket.B50_59: (50, 59),
        AgeBracket.B60_PLUS: (60, 80),
    }[bracket]


async def seed_drawings(sponsor_ids: list[str]) -> list[str]:
    print("  Seeding drawings...")
    now = datetime.datetime.utcnow()
    drawing_ids: list[str] = []
    statuses_cycle = [
        DrawingStatus.OPEN, DrawingStatus.SCHEDULED, DrawingStatus.COMPLETED,
        DrawingStatus.OPEN, DrawingStatus.DRAFT, DrawingStatus.CLOSED,
    ]
    for i in range(30):
        did = str(uuid.uuid4()).replace("-", "").upper()
        dtype = list(DrawingType)[i % 4]
        status = statuses_cycle[i % len(statuses_cycle)]
        offset_days = i - 15
        draw_time = now + datetime.timedelta(days=offset_days)
        close_time = draw_time - datetime.timedelta(hours=1)
        cost = random.choice([50, 100, 200, 500])
        await _exec(
            """
            INSERT INTO drawings (drawing_id, drawing_type, name, ticket_cost_points,
                                  drawing_time, ticket_sales_close, status)
            VALUES (HEXTORAW(:1), :2, :3, :4,
                    TO_TIMESTAMP(:5, 'YYYY-MM-DD HH24:MI:SS'),
                    TO_TIMESTAMP(:6, 'YYYY-MM-DD HH24:MI:SS'),
                    :7)
            """,
            [
                did,
                dtype.value,
                f"{dtype.value.capitalize()} Drawing #{i+1}",
                cost,
                draw_time.strftime("%Y-%m-%d %H:%M:%S"),
                close_time.strftime("%Y-%m-%d %H:%M:%S"),
                status.value,
            ],
        )
        # Add 1-3 prizes per drawing
        for rank in range(1, random.randint(2, 4)):
            pid = str(uuid.uuid4()).replace("-", "").upper()
            sponsor_id = random.choice(sponsor_ids)
            await _exec(
                """
                INSERT INTO prizes (prize_id, drawing_id, sponsor_id, rank, name,
                                    value_usd, quantity, fulfillment_type)
                VALUES (HEXTORAW(:1), HEXTORAW(:2), HEXTORAW(:3), :4, :5, :6, 1, :7)
                """,
                [
                    pid, did, sponsor_id, rank,
                    f"{'1st' if rank==1 else '2nd' if rank==2 else '3rd'} Place Prize",
                    round(random.uniform(25, 500), 2),
                    random.choice(["digital", "physical"]),
                ],
            )
        drawing_ids.append(did)
    await _commit()
    print(f"    Created {len(drawing_ids)} drawings")
    return drawing_ids


async def seed_activities(users: list[tuple[str, str]]) -> None:
    print("  Seeding activities (60-day history for 50 users)...")
    sample_users = random.sample(users, min(50, len(users)))
    count = 0
    for user_id, _ in sample_users:
        for day_offset in range(60):
            if random.random() < 0.6:  # ~60% chance of activity per day
                n_activities = random.randint(1, 3)
                for _ in range(n_activities):
                    aid = str(uuid.uuid4()).replace("-", "").upper()
                    atype = random.choice(list(ActivityType))
                    intensity = random.choice(list(Intensity))
                    duration = random.randint(15, 90)
                    points = min(1000, random.randint(20, 300))
                    start = datetime.datetime.utcnow() - datetime.timedelta(days=day_offset, hours=random.randint(6, 20))
                    end = start + datetime.timedelta(minutes=duration)
                    await _exec(
                        """
                        INSERT INTO activities (activity_id, user_id, activity_type,
                                               start_time, end_time, duration_minutes,
                                               intensity, points_earned, processed)
                        VALUES (HEXTORAW(:1), HEXTORAW(:2), :3,
                                TO_TIMESTAMP(:4, 'YYYY-MM-DD HH24:MI:SS'),
                                TO_TIMESTAMP(:5, 'YYYY-MM-DD HH24:MI:SS'),
                                :6, :7, :8, 1)
                        """,
                        [
                            aid, user_id, atype.value,
                            start.strftime("%Y-%m-%d %H:%M:%S"),
                            end.strftime("%Y-%m-%d %H:%M:%S"),
                            duration, intensity.value, points,
                        ],
                    )
                    count += 1
    await _commit()
    print(f"    Created {count} activity records")


async def seed_tickets(users: list[tuple[str, str]], drawing_ids: list[str]) -> list[tuple[str, str, str]]:
    print("  Seeding tickets (~5,000 across open drawings)...")
    open_drawings = drawing_ids[:10]  # approximate open ones for seeding
    ticket_records: list[tuple[str, str, str]] = []
    count = 0
    for user_id, _ in random.sample(users, min(100, len(users))):
        for did in random.sample(open_drawings, random.randint(1, 5)):
            n = random.randint(1, 15)
            for _ in range(n):
                tid = str(uuid.uuid4()).replace("-", "").upper()
                await _exec(
                    """
                    INSERT INTO tickets (ticket_id, drawing_id, user_id)
                    VALUES (HEXTORAW(:1), HEXTORAW(:2), HEXTORAW(:3))
                    """,
                    [tid, did, user_id],
                )
                ticket_records.append((tid, did, user_id))
                count += 1
    await _commit()
    print(f"    Created {count} tickets")
    return ticket_records


async def seed_fulfillments(ticket_records: list[tuple[str, str, str]]) -> None:
    print("  Seeding fulfillment records...")
    from fittrack.domain.enums import FulfillmentStatus

    statuses = list(FulfillmentStatus)
    sample = random.sample(ticket_records, min(8, len(ticket_records)))
    for i, (tid, did, uid) in enumerate(sample):
        fid = str(uuid.uuid4()).replace("-", "").upper()
        pid = str(uuid.uuid4()).replace("-", "").upper()
        status = statuses[i % len(statuses)]
        await _exec(
            """
            INSERT INTO prize_fulfillments (fulfillment_id, ticket_id, prize_id, user_id, status)
            VALUES (HEXTORAW(:1), HEXTORAW(:2), HEXTORAW(:3), HEXTORAW(:4), :5)
            """,
            [fid, tid, pid, uid, status.value],
        )
    await _commit()
    print(f"    Created {len(sample)} fulfillment records")


async def main() -> None:
    from fittrack.config import get_settings
    from fittrack.database.connection import close_pool, get_pool, init_pool

    settings = get_settings()
    print("Initialising connection pool...")
    await init_pool(settings)
    pool = get_pool()

    global _conn
    async with pool.acquire() as conn:
        _conn = conn

        print("Seeding data...")
        sponsor_ids = await seed_sponsors()
        users = await seed_users_and_profiles()
        drawing_ids = await seed_drawings(sponsor_ids)
        await seed_activities(users)
        ticket_records = await seed_tickets(users, drawing_ids)
        await seed_fulfillments(ticket_records)

    await close_pool()
    print("\n✓ Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
