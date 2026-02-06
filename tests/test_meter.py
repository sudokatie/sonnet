"""Tests for meter scanning module."""

import pytest
from sonnet.meter import (
    MeterType,
    get_word_stress,
    scan_line,
    get_expected_pattern,
    match_meter,
    describe_meter,
)


class TestMeterScanner:
    """Tests for meter scanning (Task 5)."""

    def test_iambic_pentameter_line(self):
        """Famous iambic pentameter line should score well."""
        line = "Shall I compare thee to a summer's day"
        score = match_meter(line, MeterType.IAMBIC, 10)
        assert score >= 0.6  # Should be reasonably close

    def test_trochaic_line(self):
        """Trochaic pattern detection."""
        # "Double, double, toil and trouble" is trochaic
        score = match_meter("Double double toil and trouble", MeterType.TROCHAIC, 10)
        assert score >= 0.5

    def test_stress_pattern_extraction(self):
        """Word stress patterns are extracted."""
        pattern = get_word_stress("poetry")
        assert pattern  # Should have a pattern
        assert len(pattern) == 3  # 3 syllables

    def test_unknown_word_heuristic(self):
        """Unknown words use heuristic."""
        pattern = get_word_stress("xyzzyword")
        assert pattern  # Should still return something
        assert all(c in "u/" for c in pattern)

    def test_empty_line(self):
        """Empty line returns empty pattern."""
        assert scan_line("") == ""

    def test_single_word_line(self):
        """Single word line works."""
        pattern = scan_line("hello")
        assert len(pattern) == 2  # hello = 2 syllables

    def test_match_score_perfect(self):
        """Perfect match scores 1.0."""
        # Construct a line that should match iambic exactly
        expected = get_expected_pattern(MeterType.IAMBIC, 4)
        # Score comparing identical patterns
        from sonnet.meter import _pattern_similarity
        assert _pattern_similarity(expected, expected) == 1.0

    def test_match_score_opposite(self):
        """Opposite pattern scores low."""
        from sonnet.meter import _pattern_similarity
        # Iambic vs trochaic are opposites
        iambic = "u/u/u/"
        trochaic = "/u/u/u"
        score = _pattern_similarity(iambic, trochaic)
        assert score < 0.5

    def test_match_score_zero_for_empty(self):
        """Empty patterns return 0."""
        score = match_meter("", MeterType.IAMBIC)
        assert score == 0.0


class TestExpectedPatterns:
    """Tests for expected pattern generation."""

    def test_iambic_pentameter_pattern(self):
        """Iambic pentameter = u/u/u/u/u/"""
        pattern = get_expected_pattern(MeterType.IAMBIC, 10)
        assert pattern == "u/u/u/u/u/"

    def test_iambic_tetrameter(self):
        """Iambic tetrameter = 8 syllables."""
        pattern = get_expected_pattern(MeterType.IAMBIC, 8)
        assert pattern == "u/u/u/u/"

    def test_trochaic_pattern(self):
        """Trochaic = /u/u/u..."""
        pattern = get_expected_pattern(MeterType.TROCHAIC, 8)
        assert pattern == "/u/u/u/u"

    def test_anapestic_pattern(self):
        """Anapestic = uu/uu/..."""
        pattern = get_expected_pattern(MeterType.ANAPESTIC, 9)
        assert pattern == "uu/uu/uu/"


class TestWordStress:
    """Tests for word stress extraction."""

    def test_hello(self):
        pattern = get_word_stress("hello")
        assert len(pattern) == 2

    def test_the(self):
        pattern = get_word_stress("the")
        assert len(pattern) >= 1

    def test_contraction(self):
        pattern = get_word_stress("don't")
        assert len(pattern) >= 1


class TestDescribeMeter:
    """Tests for meter description."""

    def test_iambic_pentameter(self):
        desc = describe_meter(MeterType.IAMBIC, 5)
        assert "iambic" in desc
        assert "pentameter" in desc

    def test_trochaic_tetrameter(self):
        desc = describe_meter(MeterType.TROCHAIC, 4)
        assert "trochaic" in desc
        assert "tetrameter" in desc
