# ADR-0004: Computed tier code derivation and encoding

**Status:** Accepted  
**Date:** 2026-06-01  
**Deciders:** FitTrack engineering

---

## Context

FitTrack structures sweepstakes competition across **30 demographic tiers** to ensure users compete on a level playing field. Each tier is the intersection of:

- **Biological sex** — `M` or `F` (2 values)
- **Age bracket** — `18-29`, `30-39`, `40-49`, `50-59`, `60+` (5 values)
- **Fitness level** — `beginner` (`BEG`), `intermediate` (`INT`), `advanced` (`ADV`) (3 values)

2 × 5 × 3 = **30 tiers**.

The tier determines which leaderboard a user appears on and which drawing pool they enter. It must be:
1. Computable from profile fields (sex, date of birth, fitness level).
2. Stable within a period (a user's tier does not change mid-drawing).
3. Updateable when the user changes their fitness level or, more rarely, crosses an age bracket boundary.
4. Queryable efficiently — leaderboard queries filter by tier code.
5. Human-readable in logs and admin tools.

The design question: how should the tier be stored and maintained?

---

## Decision

The tier code is a **computed, derived string** encoded as `{SEX}-{AGE_BRACKET}-{ABBREV}`, e.g. `F-30-39-INT`. It is:

- **Stored** as a plain `VARCHAR2(20)` column on the `profiles` table with an index (`idx_profiles_tier`), so it can be queried directly.
- **Never treated as the source of truth** for tier membership. If `biological_sex`, `date_of_birth`, or `fitness_level` change, the tier code must be recomputed by calling `services.tiers.recalculate()`. The stored string is a cache of the derived value, not the authoritative definition.
- **Computed** by a pure function `compute_tier_code(sex, age_bracket, fitness_level)` in `src/fittrack/domain/tier.py` with 100% unit-test coverage.

Age bracket is itself derived from date of birth via `domain.age.bracket_from_age()`, which is called at profile upsert time. Heart-rate zones (intensity buckets) also re-derive from age on profile updates — no stale state is tolerated at profile write time.

---

## Alternatives Considered

| Option | Why Rejected |
|--------|-------------|
| **Tier ID foreign key** (lookup table with 30 rows) | Normalised, avoids the "stored derived value" problem. Rejected because it adds a join for every leaderboard query and makes the tier opaque to humans reading logs or admin tools. The 30-row lookup table also never changes (tier definitions are fixed for MVP), so the normalisation benefit is minimal. |
| **Compute on-the-fly, never store** | Eliminates stale-state risk entirely. Rejected because every leaderboard query would need a join to `profiles` and a substring/decode — functional indexes can express this but make the query planner harder to reason about at scale. Storing the string directly enables a simple `WHERE tier_code = :1` with a B-tree index. |
| **Bitmask or integer encoding** | Compact and sortable. Rejected: opaque in logs, requires decoding in every query result, and age bracket range queries (`30-39` < `40-49`) would need a mapping table anyway. Human-readable encoding was chosen for maintainability. |
| **Separate `tier_assignments` table** (history + current) | Would support auditing tier changes over time and prevent mid-period tier reassignment. Rejected for MVP — the complexity is not yet justified. If fairness complaints around mid-period tier changes arise, a `tier_assignments` history table is the right v1.1 upgrade path. |

---

## Encoding Format

```
{SEX}-{AGE_BRACKET}-{LEVEL_ABBREV}

SEX          : M | F
AGE_BRACKET  : 18-29 | 30-39 | 40-49 | 50-59 | 60+
LEVEL_ABBREV : BEG | INT | ADV

Examples: M-18-29-BEG  F-30-39-INT  M-60+-ADV
```

The regex `[MF]-(?:18-29|30-39|40-49|50-59|60\+)-(?:BEG|INT|ADV)` is enforced in `TierCode.parse()` and in the `TIER_CODE_PATTERN` constant in `domain/tier.py`.

---

## Consequences

**Positive:**
- Leaderboard queries are a direct `WHERE tier_code = :1` with a single B-tree index — no joins, no decode.
- Tier code is self-documenting in logs (`F-30-39-INT` is immediately readable).
- The pure `compute_tier_code()` function has no side effects and is easy to test exhaustively with Hypothesis.
- Age bracket and fitness level are exposed in the stored format, so admin queries like "how many users are in each age group" require no decode.

**Negative:**
- Stored derived values create a staleness risk: if profile fields change and `recalculate()` is not called, the stored tier code drifts. Mitigated by: (a) all profile writes go through `profiles_repo.upsert_profile()` which calls the recalculate path, and (b) the `CLAUDE.md` "Gotchas" section explicitly warns against setting `tier_code` directly.
- Age bracket changes silently if a user's birthday crosses a bracket boundary between profile updates. For MVP, tier codes are only recalculated on explicit profile saves, not automatically on birthdays. This is acceptable because tier membership changes at most once per year per user, and drawings run daily.

**Neutral:**
- The `60+` bracket requires escaping the `+` character in regex and URL parameters. This is handled in `TierCode.parse()`.
- If a fourth sex category or a sixth age bracket is added post-MVP, both the domain enum and the stored codes must be migrated. The isolated domain module makes this a contained change.

---

## References

- `src/fittrack/domain/tier.py` — `compute_tier_code()`, `TierCode.parse()`, `TIER_CODE_PATTERN`
- `src/fittrack/domain/age.py` — `bracket_from_age()`
- `src/fittrack/domain/enums.py` — `FitnessLevel`, `Sex`, `AgeBracket`
- `tests/unit/test_tier.py` — exhaustive tier code tests
- `CLAUDE.md` — "Tier code is computed" and "Heart rate zones depend on user age" gotchas
