"""Unit tests for state eligibility."""

from __future__ import annotations

import pytest

from fittrack.domain.states import ELIGIBLE_STATES, INELIGIBLE_STATES, is_eligible_state


@pytest.mark.unit
class TestEligibleStates:
    def test_ineligible_states_excluded(self) -> None:
        for code in ("NY", "FL", "RI"):
            assert code not in ELIGIBLE_STATES, f"{code} should not be in ELIGIBLE_STATES"

    def test_ineligible_states_set(self) -> None:
        assert "NY" in INELIGIBLE_STATES
        assert "FL" in INELIGIBLE_STATES
        assert "RI" in INELIGIBLE_STATES

    def test_common_eligible_states_present(self) -> None:
        for code in ("CA", "TX", "WA", "CO", "IL", "GA", "AZ", "MA"):
            assert code in ELIGIBLE_STATES, f"{code} should be in ELIGIBLE_STATES"

    def test_all_eligible_are_valid_us_state_codes(self) -> None:
        for code in ELIGIBLE_STATES:
            assert len(code) == 2, f"State code '{code}' must be 2 chars"
            assert code.isupper(), f"State code '{code}' must be uppercase"

    def test_eligible_count(self) -> None:
        # 50 states + DC = 51 total; MVP excludes NY, FL, RI → 48 eligible
        assert len(ELIGIBLE_STATES) == 48

    def test_no_overlap_between_eligible_and_ineligible(self) -> None:
        assert ELIGIBLE_STATES.isdisjoint(INELIGIBLE_STATES)


@pytest.mark.unit
class TestIsEligibleState:
    def test_eligible_state_returns_true(self) -> None:
        assert is_eligible_state("CA") is True
        assert is_eligible_state("TX") is True

    def test_ineligible_state_returns_false(self) -> None:
        assert is_eligible_state("NY") is False
        assert is_eligible_state("FL") is False
        assert is_eligible_state("RI") is False

    def test_case_insensitive(self) -> None:
        assert is_eligible_state("ca") is True
        assert is_eligible_state("ny") is False
        assert is_eligible_state("Tx") is True

    def test_unknown_state_returns_false(self) -> None:
        assert is_eligible_state("XX") is False
        assert is_eligible_state("") is False
        assert is_eligible_state("ZZ") is False
