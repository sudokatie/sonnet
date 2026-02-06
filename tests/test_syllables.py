"""Tests for syllable counting module."""

import pytest
from sonnet.syllables import (
    get_cmu_dict,
    get_phonemes,
    count_syllables,
    count_syllables_cmu,
    count_syllables_detailed,
    count_line_syllables,
    _heuristic_count,
)


class TestCMUDictLoader:
    """Tests for CMU dictionary loading (Task 2)."""

    def test_dictionary_loads(self):
        """Dictionary loads successfully."""
        cmu = get_cmu_dict()
        assert cmu is not None
        assert isinstance(cmu, dict)

    def test_dictionary_has_entries(self):
        """Dictionary has substantial entries."""
        cmu = get_cmu_dict()
        assert len(cmu) > 100000

    def test_common_word_the(self):
        """Common word 'the' is found."""
        cmu = get_cmu_dict()
        assert "the" in cmu

    def test_common_word_poetry(self):
        """Word 'poetry' is found."""
        cmu = get_cmu_dict()
        assert "poetry" in cmu

    def test_common_word_sonnet(self):
        """Word 'sonnet' is found."""
        cmu = get_cmu_dict()
        assert "sonnet" in cmu

    def test_phoneme_format(self):
        """Phonemes are list of strings."""
        cmu = get_cmu_dict()
        assert "hello" in cmu
        phonemes = cmu["hello"][0]
        assert isinstance(phonemes, list)
        assert all(isinstance(p, str) for p in phonemes)

    def test_multiple_pronunciations(self):
        """Words with multiple pronunciations handled."""
        cmu = get_cmu_dict()
        # 'a' has multiple pronunciations: AH0 and EY1
        assert "a" in cmu
        assert len(cmu["a"]) >= 2

    def test_case_insensitive(self):
        """Lookup is case insensitive."""
        cmu = get_cmu_dict()
        assert "hello" in cmu
        # All keys should be lowercase
        assert all(k == k.lower() for k in list(cmu.keys())[:100])

    def test_word_not_found(self):
        """Unknown word returns None for phonemes."""
        phonemes = get_phonemes("xyzzyplugh")
        assert phonemes is None

    def test_empty_string(self):
        """Empty string returns None."""
        phonemes = get_phonemes("")
        assert phonemes is None

    def test_stress_markers_present(self):
        """Phonemes contain stress markers (0, 1, 2)."""
        cmu = get_cmu_dict()
        phonemes = cmu["poetry"][0]
        # Should have vowels with stress markers
        has_stress = any(p[-1].isdigit() for p in phonemes)
        assert has_stress

    def test_get_phonemes_returns_first(self):
        """get_phonemes returns first pronunciation."""
        phonemes = get_phonemes("hello")
        assert phonemes is not None
        assert isinstance(phonemes, list)

    def test_cache_works(self):
        """Second call uses cached dictionary."""
        import time
        start = time.time()
        cmu1 = get_cmu_dict()
        first_time = time.time() - start
        
        start = time.time()
        cmu2 = get_cmu_dict()
        second_time = time.time() - start
        
        assert cmu1 is cmu2  # Same object
        assert second_time < first_time or second_time < 0.01

    def test_punctuation_stripped(self):
        """Punctuation in word is handled."""
        phonemes = get_phonemes("hello!")
        assert phonemes is not None


class TestSyllableCounter:
    """Tests for syllable counting (Task 3)."""

    # Single syllable words
    def test_single_syllable_cat(self):
        assert count_syllables("cat") == 1

    def test_single_syllable_dog(self):
        assert count_syllables("dog") == 1

    def test_single_syllable_the(self):
        assert count_syllables("the") == 1

    # Multi-syllable words
    def test_poetry_three_syllables(self):
        assert count_syllables("poetry") == 3

    def test_beautiful_three_syllables(self):
        assert count_syllables("beautiful") == 3

    def test_hello_two_syllables(self):
        assert count_syllables("hello") == 2

    # Heuristic fallback
    def test_unknown_word_heuristic(self):
        """Unknown word falls back to heuristic."""
        count, source = count_syllables_detailed("xyzzyword")
        assert count >= 1
        assert source == "heuristic"

    def test_known_word_uses_cmu(self):
        """Known word uses CMU dictionary."""
        count, source = count_syllables_detailed("poetry")
        assert count == 3
        assert source == "cmu"

    # Silent-e handling
    def test_silent_e_make(self):
        assert count_syllables("make") == 1

    def test_silent_e_recipe(self):
        # Recipe has 3 syllables, not affected by simple silent-e rule
        assert count_syllables("recipe") == 3

    # Contractions
    def test_contraction_dont(self):
        assert count_syllables("don't") == 1

    # Empty and edge cases
    def test_empty_string(self):
        assert count_syllables("") == 0

    def test_whitespace_only(self):
        assert count_syllables("   ") == 0

    # Case handling
    def test_lowercase(self):
        assert count_syllables("hello") == 2

    def test_uppercase(self):
        assert count_syllables("HELLO") == 2

    def test_mixed_case(self):
        assert count_syllables("HeLLo") == 2

    # Suffixes
    def test_suffix_tion(self):
        assert count_syllables("nation") == 2

    def test_suffix_ed_walked(self):
        # "walked" is 1 syllable
        assert count_syllables("walked") == 1

    def test_suffix_ed_wanted(self):
        # "wanted" is 2 syllables
        assert count_syllables("wanted") == 2

    # Line counting
    def test_line_simple(self):
        assert count_line_syllables("old pond frog") == 3

    def test_line_with_punctuation(self):
        assert count_line_syllables("Hello, world!") == 3

    def test_line_empty(self):
        assert count_line_syllables("") == 0

    def test_line_haiku_first(self):
        # "An old silent pond" = 5 syllables
        result = count_line_syllables("An old silent pond")
        assert result == 5

    # Edge cases
    def test_queue_one_syllable(self):
        assert count_syllables("queue") == 1

    def test_hyphenated_word(self):
        # Hyphenated words should work
        count = count_syllables("self-esteem")
        assert count >= 2


class TestHeuristic:
    """Tests for heuristic syllable counting."""

    def test_simple_vowel_count(self):
        assert _heuristic_count("cat") == 1

    def test_multiple_vowels(self):
        assert _heuristic_count("beautiful") >= 3

    def test_consecutive_vowels(self):
        # "boat" has 2 vowels but 1 syllable
        assert _heuristic_count("boat") == 1

    def test_silent_e(self):
        assert _heuristic_count("make") == 1

    def test_minimum_one(self):
        # Even weird input should return at least 1
        assert _heuristic_count("xyz") >= 1
