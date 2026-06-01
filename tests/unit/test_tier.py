"""Unit tests for tier code computation."""

from __future__ import annotations

import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fittrack.domain.age import AgeBracket
from fittrack.domain.enums import FitnessLevel, Sex
from fittrack.domain.tier import TIER_CODE_PATTERN, TierCode, compute_tier_code


@pytest.mark.unit
class TestComputeTierCode:
    def test_male_18_29_beginner(self) -> None:
        result = compute_tier_code(Sex.MALE, AgeBracket.B18_29, FitnessLevel.BEGINNER)
        assert result == "M-18-29-BEG"

    def test_female_30_39_intermediate(self) -> None:
        result = compute_tier_code(Sex.FEMALE, AgeBracket.B30_39, FitnessLevel.INTERMEDIATE)
        assert result == "F-30-39-INT"

    def test_female_40_49_advanced(self) -> None:
        result = compute_tier_code(Sex.FEMALE, AgeBracket.B40_49, FitnessLevel.ADVANCED)
        assert result == "F-40-49-ADV"

    def test_male_60_plus_advanced(self) -> None:
        result = compute_tier_code(Sex.MALE, AgeBracket.B60_PLUS, FitnessLevel.ADVANCED)
        assert result == "M-60+-ADV"

    def test_female_50_59_beginner(self) -> None:
        result = compute_tier_code(Sex.FEMALE, AgeBracket.B50_59, FitnessLevel.BEGINNER)
        assert result == "F-50-59-BEG"


@pytest.mark.unit
class TestTierCodePattern:
    def test_valid_codes_match_pattern(self) -> None:
        valid = [
            "M-18-29-BEG",
            "F-30-39-INT",
            "M-40-49-ADV",
            "F-50-59-BEG",
            "M-60+-INT",
        ]
        for code in valid:
            assert re.match(TIER_CODE_PATTERN, code), f"'{code}' should match pattern"

    def test_invalid_codes_reject(self) -> None:
        invalid = [
            "X-18-29-BEG",   # invalid sex
            "M-25-30-BEG",   # invalid bracket
            "F-30-39-MED",   # invalid level
            "m-18-29-beg",   # lowercase
            "",
            "M-18-29",       # missing level
        ]
        for code in invalid:
            assert not re.match(TIER_CODE_PATTERN, code), f"'{code}' should not match pattern"


@pytest.mark.unit
class TestTierCodeTotal:
    def test_exactly_30_unique_tier_codes(self) -> None:
        codes = set()
        for sex in Sex:
            for bracket in AgeBracket:
                for level in FitnessLevel:
                    code = compute_tier_code(sex, bracket, level)
                    codes.add(code)
        assert len(codes) == 30

    def test_all_codes_match_pattern(self) -> None:
        for sex in Sex:
            for bracket in AgeBracket:
                for level in FitnessLevel:
                    code = compute_tier_code(sex, bracket, level)
                    assert re.match(TIER_CODE_PATTERN, code), f"'{code}' should match pattern"


@pytest.mark.unit
class TestTierCodeNamedTuple:
    def test_parse_known_code(self) -> None:
        tc = TierCode.parse("M-30-39-INT")
        assert tc.sex == Sex.MALE
        assert tc.bracket == AgeBracket.B30_39
        assert tc.level == FitnessLevel.INTERMEDIATE

    def test_round_trip(self) -> None:
        original = "F-40-49-ADV"
        tc = TierCode.parse(original)
        assert tc.code == original

    def test_parse_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            TierCode.parse("INVALID")

    def test_parse_all_30_codes(self) -> None:
        for sex in Sex:
            for bracket in AgeBracket:
                for level in FitnessLevel:
                    code = compute_tier_code(sex, bracket, level)
                    tc = TierCode.parse(code)
                    assert tc.code == code


@pytest.mark.unit
class TestTierCodeHypothesis:
    @given(
        sex=st.sampled_from(list(Sex)),
        bracket=st.sampled_from(list(AgeBracket)),
        level=st.sampled_from(list(FitnessLevel)),
    )
    @settings(max_examples=100)
    def test_compute_always_produces_valid_code(
        self, sex: Sex, bracket: AgeBracket, level: FitnessLevel
    ) -> None:
        code = compute_tier_code(sex, bracket, level)
        assert re.match(TIER_CODE_PATTERN, code)
        # round-trip
        assert TierCode.parse(code).code == code
