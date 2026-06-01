"""Unit tests for age bracket helpers."""

from __future__ import annotations

import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fittrack.domain.age import AgeBracket, age_from_dob, bracket_from_age


@pytest.mark.unit
class TestAgeBracket:
    def test_values(self) -> None:
        assert AgeBracket.B18_29.value == "18-29"
        assert AgeBracket.B30_39.value == "30-39"
        assert AgeBracket.B40_49.value == "40-49"
        assert AgeBracket.B50_59.value == "50-59"
        assert AgeBracket.B60_PLUS.value == "60+"

    def test_all_brackets(self) -> None:
        values = {b.value for b in AgeBracket}
        assert values == {"18-29", "30-39", "40-49", "50-59", "60+"}

    def test_five_brackets(self) -> None:
        assert len(AgeBracket) == 5


@pytest.mark.unit
class TestBracketFromAge:
    def test_lower_bound_18(self) -> None:
        assert bracket_from_age(18) == AgeBracket.B18_29

    def test_upper_bound_29(self) -> None:
        assert bracket_from_age(29) == AgeBracket.B18_29

    def test_30_39_range(self) -> None:
        assert bracket_from_age(30) == AgeBracket.B30_39
        assert bracket_from_age(35) == AgeBracket.B30_39
        assert bracket_from_age(39) == AgeBracket.B30_39

    def test_40_49_range(self) -> None:
        assert bracket_from_age(40) == AgeBracket.B40_49
        assert bracket_from_age(45) == AgeBracket.B40_49
        assert bracket_from_age(49) == AgeBracket.B40_49

    def test_50_59_range(self) -> None:
        assert bracket_from_age(50) == AgeBracket.B50_59
        assert bracket_from_age(55) == AgeBracket.B50_59
        assert bracket_from_age(59) == AgeBracket.B50_59

    def test_60_plus(self) -> None:
        assert bracket_from_age(60) == AgeBracket.B60_PLUS
        assert bracket_from_age(75) == AgeBracket.B60_PLUS
        assert bracket_from_age(100) == AgeBracket.B60_PLUS

    def test_under_18_raises(self) -> None:
        with pytest.raises(ValueError, match="18"):
            bracket_from_age(17)

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="18"):
            bracket_from_age(0)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="18"):
            bracket_from_age(-1)


@pytest.mark.unit
class TestAgeFromDob:
    def test_exact_birthday_today(self) -> None:
        today = datetime.date.today()
        dob = today.replace(year=today.year - 25)
        assert age_from_dob(dob) == 25

    def test_birthday_not_yet_this_year(self) -> None:
        today = datetime.date.today()
        # DOB one day in the future within the year → one year younger
        next_birthday = today + datetime.timedelta(days=1)
        dob = next_birthday.replace(year=next_birthday.year - 30)
        assert age_from_dob(dob) == 29

    def test_birthday_already_passed_this_year(self) -> None:
        today = datetime.date.today()
        past_birthday = today - datetime.timedelta(days=1)
        dob = past_birthday.replace(year=past_birthday.year - 30)
        assert age_from_dob(dob) == 30

    def test_specific_known_date(self) -> None:
        # Born 1990-01-01, reference date 2026-05-29 → age 36
        dob = datetime.date(1990, 1, 1)
        assert age_from_dob(dob, reference=datetime.date(2026, 5, 29)) == 36

    def test_birthday_on_reference_date(self) -> None:
        ref = datetime.date(2026, 5, 29)
        dob = datetime.date(1996, 5, 29)
        assert age_from_dob(dob, reference=ref) == 30


@pytest.mark.unit
class TestAgeBracketHypothesis:
    @given(age=st.integers(min_value=18, max_value=120))
    @settings(max_examples=200)
    def test_every_valid_age_maps_to_a_bracket(self, age: int) -> None:
        result = bracket_from_age(age)
        assert isinstance(result, AgeBracket)

    @given(age=st.integers(max_value=17))
    @settings(max_examples=50)
    def test_underage_always_raises(self, age: int) -> None:
        with pytest.raises(ValueError):
            bracket_from_age(age)
