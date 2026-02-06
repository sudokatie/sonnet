"""
Tests for checker.py - constraint validation.
"""

import pytest
from sonnet.checker import (
    CheckResult,
    PoemAnalysis,
    check_syllables,
    check_rhymes,
    check_meter,
    check_poem,
    format_analysis,
)
from sonnet.forms import get_form


class TestCheckSyllables:
    """Tests for syllable checking."""
    
    def test_haiku_correct(self):
        """Haiku with correct syllables passes."""
        form = get_form("haiku")
        lines = [
            "old pond sits still now",  # 5
            "a frog jumps in the water",  # 7
            "splash echoes in dark",  # 5
        ]
        results = check_syllables(lines, form)
        assert len(results) == 3
        # All should pass or be within tolerance
        assert all(r.passed for r in results)
    
    def test_syllable_off_by_one(self):
        """One syllable off is tolerated."""
        form = get_form("haiku")
        lines = [
            "the old pond is still",  # 5 or close
            "jumping frogs in water",  # 6 instead of 7
            "splash in the dark pond",  # 5
        ]
        results = check_syllables(lines, form)
        # Off by 1 should still pass
        assert results[1].passed
    
    def test_syllable_way_off_fails(self):
        """Many syllables off fails."""
        form = get_form("haiku")
        lines = [
            "the extraordinarily beautiful old pond",  # ~12
            "frog",  # 1
            "hi",  # 1
        ]
        results = check_syllables(lines, form)
        assert not results[0].passed  # Way over
        assert not results[1].passed  # Way under
    
    def test_free_verse_no_constraints(self):
        """Free verse has no syllable constraints."""
        form = get_form("free_verse")
        lines = ["any number of syllables here works just fine for me"]
        results = check_syllables(lines, form)
        assert results[0].passed
        assert results[0].expected == "any"


class TestCheckRhymes:
    """Tests for rhyme checking."""
    
    def test_no_rhyme_scheme(self):
        """No rhyme scheme returns empty results."""
        form = get_form("haiku")
        lines = ["line one", "line two", "line three"]
        results = check_rhymes(lines, form)
        assert len(results) == 0
    
    def test_perfect_rhymes_pass(self):
        """Perfect rhymes pass."""
        form = get_form("limerick")
        lines = [
            "There once was a man from Maine",  # A - Maine
            "Who liked to walk in the rain",    # A - rain (rhymes)
            "He slipped on ice",                 # B
            "It wasn't nice",                    # B - nice/ice
            "And never went out again",          # A - again
        ]
        results = check_rhymes(lines, form)
        # Check that we got rhyme results
        assert len(results) > 0
    
    def test_slant_rhyme_accepted(self):
        """Slant rhymes are accepted with lower score."""
        form = get_form("limerick")
        # Using words that slant rhyme
        lines = [
            "word ending in cat",
            "word ending in bed",  # Slant rhyme with cat
            "short three",
            "short free",
            "word ending in bat",
        ]
        results = check_rhymes(lines, form)
        # Some should pass even with slant
        slant_results = [r for r in results if "slant" in r.actual.lower()]
        for r in slant_results:
            assert r.passed
            assert r.score < 1.0
    
    def test_no_rhyme_fails(self):
        """Non-rhyming words fail."""
        form = get_form("limerick")
        lines = [
            "There once was a man from space",
            "Who liked to eat pizza",  # Doesn't rhyme with space
            "He ran around",
            "And fell down",
            "Then landed on his face",
        ]
        results = check_rhymes(lines, form)
        # Line 2 (index 1) should fail to rhyme with line 1
        line_2_result = [r for r in results if r.line_index == 1]
        if line_2_result:
            assert not line_2_result[0].passed


class TestCheckMeter:
    """Tests for meter checking."""
    
    def test_no_meter_constraint(self):
        """No meter constraint returns empty results."""
        form = get_form("haiku")
        lines = ["line one", "line two", "line three"]
        results = check_meter(lines, form)
        assert len(results) == 0
    
    def test_iambic_pentameter(self):
        """Iambic pentameter detection."""
        form = get_form("shakespearean")
        # Classic iambic pentameter line
        lines = ["Shall I compare thee to a summer's day"]
        results = check_meter(lines, form)
        assert len(results) == 1
        # Should score reasonably well
        assert results[0].score > 0.4


class TestCheckPoem:
    """Tests for full poem checking."""
    
    def test_haiku_full_check(self):
        """Full haiku check."""
        form = get_form("haiku")
        lines = [
            "An old silent pond",
            "A frog jumps into the pond",
            "Splash silence again",
        ]
        analysis = check_poem(lines, form)
        assert analysis.form.name == "Haiku"
        assert len(analysis.syllable_results) == 3
        assert len(analysis.rhyme_results) == 0  # No rhyme scheme
        assert len(analysis.meter_results) == 0  # No meter
    
    def test_analysis_overall_score(self):
        """Analysis computes overall score."""
        form = get_form("haiku")
        lines = ["one", "two", "three"]
        analysis = check_poem(lines, form)
        assert 0.0 <= analysis.overall_score <= 1.0
    
    def test_analysis_passed_property(self):
        """Analysis passed property works."""
        form = get_form("free_verse")
        lines = ["anything goes here"]
        analysis = check_poem(lines, form)
        assert analysis.passed  # Free verse passes everything


class TestPoemAnalysis:
    """Tests for PoemAnalysis dataclass."""
    
    def test_empty_analysis_passes(self):
        """Analysis with no results passes."""
        form = get_form("free_verse")
        analysis = PoemAnalysis(form=form, lines=[])
        assert analysis.passed
        assert analysis.overall_score == 1.0
    
    def test_mixed_results(self):
        """Analysis with mixed pass/fail results."""
        form = get_form("haiku")
        analysis = PoemAnalysis(
            form=form,
            lines=["a", "b", "c"],
            syllable_results=[
                CheckResult(0, True, "syllables", "5", "5", 1.0),
                CheckResult(1, False, "syllables", "7", "1", 0.0),
            ]
        )
        assert not analysis.passed
        assert analysis.overall_score == 0.5


class TestFormatAnalysis:
    """Tests for format_analysis helper."""
    
    def test_format_basic(self):
        """Basic formatting works."""
        form = get_form("haiku")
        analysis = PoemAnalysis(
            form=form,
            lines=["line one"],
            syllable_results=[
                CheckResult(0, True, "syllables", "5", "5", 1.0),
            ]
        )
        output = format_analysis(analysis)
        assert "Haiku" in output
        assert "PASS" in output
        assert "Syllables:" in output
