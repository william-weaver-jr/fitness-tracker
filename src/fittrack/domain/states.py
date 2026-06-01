"""US state eligibility for sweepstakes participation."""

from __future__ import annotations

# States excluded from MVP due to sweepstakes registration requirements.
INELIGIBLE_STATES: frozenset[str] = frozenset({"NY", "FL", "RI"})

# All US states + DC (51 total), minus the 3 ineligible = 48 eligible.
_ALL_US_STATES: frozenset[str] = frozenset(
    {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC",
        "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA",
        "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE",
        "NV", "NH", "NJ", "NM", "NC", "ND", "OH", "OK", "OR",
        "PA", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA",
        "WV", "WI", "WY",
    }
)

ELIGIBLE_STATES: frozenset[str] = _ALL_US_STATES - INELIGIBLE_STATES


def is_eligible_state(state: str) -> bool:
    """Return True if *state* (2-letter code, case-insensitive) may participate."""
    return state.upper() in ELIGIBLE_STATES
