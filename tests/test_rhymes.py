"""Tests for rhyme detection module."""

import pytest
from sonnet.rhymes import (
    RhymeType,
    check_rhyme,
    find_rhymes,
    get_rhyme_phonemes,
    get_rhyme_groups,
    get_last_word,
)


class TestRhymeDetection:
    """Tests for rhyme detection (Task 4)."""

    # Perfect rhymes
    def test_perfect_rhyme_cat_hat(self):
        assert check_rhyme("cat", "hat") == RhymeType.PERFECT

    def test_perfect_rhyme_love_dove(self):
        assert check_rhyme("love", "dove") == RhymeType.PERFECT

    def test_perfect_rhyme_moon_june(self):
        assert check_rhyme("moon", "June") == RhymeType.PERFECT

    def test_perfect_rhyme_day_way(self):
        assert check_rhyme("day", "way") == RhymeType.PERFECT

    def test_perfect_rhyme_night_sight(self):
        assert check_rhyme("night", "sight") == RhymeType.PERFECT

    # Slant rhymes
    def test_slant_rhyme_cat_bed(self):
        # Cat and bed don't perfectly rhyme but might slant
        result = check_rhyme("cat", "bed")
        assert result in (RhymeType.SLANT, RhymeType.NONE)

    def test_slant_rhyme_time_mine(self):
        result = check_rhyme("time", "mine")
        assert result in (RhymeType.PERFECT, RhymeType.SLANT)

    # No rhyme
    def test_no_rhyme_cat_dog(self):
        assert check_rhyme("cat", "dog") == RhymeType.NONE

    def test_no_rhyme_love_move(self):
        # Eye rhyme but not sound rhyme
        result = check_rhyme("love", "move")
        # These don't rhyme phonetically
        assert result in (RhymeType.NONE, RhymeType.SLANT)

    # Same word
    def test_same_word_rhymes(self):
        assert check_rhyme("love", "love") == RhymeType.PERFECT

    # Unknown words
    def test_unknown_word_returns_none(self):
        assert check_rhyme("xyzzy", "plugh") == RhymeType.NONE

    # Case insensitive
    def test_case_insensitive(self):
        assert check_rhyme("CAT", "hat") == RhymeType.PERFECT
        assert check_rhyme("cat", "HAT") == RhymeType.PERFECT

    # Multi-syllable rhymes
    def test_multi_syllable_poetry_history(self):
        result = check_rhyme("poetry", "history")
        assert result in (RhymeType.PERFECT, RhymeType.SLANT)

    def test_multi_syllable_nation_station(self):
        assert check_rhyme("nation", "station") == RhymeType.PERFECT


class TestRhymePhonemes:
    """Tests for rhyme phoneme extraction."""

    def test_phoneme_extraction(self):
        phonemes = get_rhyme_phonemes("cat")
        assert phonemes is not None
        assert len(phonemes) >= 1

    def test_unknown_word(self):
        assert get_rhyme_phonemes("xyzzyplugh") is None

    def test_stressed_vowel_found(self):
        phonemes = get_rhyme_phonemes("poetry")
        assert phonemes is not None


class TestFindRhymes:
    """Tests for finding rhymes from candidates."""

    def test_find_rhymes_basic(self):
        candidates = ["hat", "dog", "bat", "cat"]
        rhymes = find_rhymes("rat", candidates)
        words = [r[0] for r in rhymes]
        assert "hat" in words
        assert "bat" in words
        assert "cat" in words
        assert "dog" not in words

    def test_empty_candidates(self):
        assert find_rhymes("cat", []) == []

    def test_empty_word(self):
        assert find_rhymes("", ["hat", "bat"]) == []

    def test_sort_by_quality(self):
        # Perfect rhymes should come first
        candidates = ["cat", "bed", "hat"]
        rhymes = find_rhymes("rat", candidates)
        if len(rhymes) >= 2:
            # All should be perfect for rat/cat/hat
            assert rhymes[0][1] == RhymeType.PERFECT

    def test_include_slant_false(self):
        candidates = ["hat", "bet"]  # bet might be slant
        rhymes = find_rhymes("cat", candidates, include_slant=False)
        for word, rtype in rhymes:
            assert rtype == RhymeType.PERFECT


class TestRhymeGroups:
    """Tests for rhyme scheme parsing."""

    def test_aabb(self):
        groups = get_rhyme_groups("AABB")
        assert groups == {"A": [0, 1], "B": [2, 3]}

    def test_abab(self):
        groups = get_rhyme_groups("ABAB")
        assert groups == {"A": [0, 2], "B": [1, 3]}

    def test_shakespearean(self):
        groups = get_rhyme_groups("ABABCDCDEFEFGG")
        assert groups["A"] == [0, 2]
        assert groups["B"] == [1, 3]
        assert groups["G"] == [12, 13]

    def test_lowercase(self):
        groups = get_rhyme_groups("abab")
        assert groups == {"A": [0, 2], "B": [1, 3]}


class TestLastWord:
    """Tests for extracting last word from line."""

    def test_simple(self):
        assert get_last_word("hello world") == "world"

    def test_with_punctuation(self):
        assert get_last_word("hello world!") == "world"

    def test_empty(self):
        assert get_last_word("") == ""

    def test_single_word(self):
        assert get_last_word("hello") == "hello"
