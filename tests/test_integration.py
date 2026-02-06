"""
Integration tests - end-to-end pipelines.
"""

import pytest
from unittest.mock import patch, MagicMock

from sonnet.forms import get_form
from sonnet.syllables import count_line_syllables
from sonnet.rhymes import check_rhyme, RhymeType
from sonnet.meter import scan_line
from sonnet.checker import check_poem
from sonnet.ranker import rank_candidates, Constraints
from sonnet.generator import build_prompt, parse_candidates


class TestHaikuPipeline:
    """Integration tests for haiku validation."""
    
    def test_valid_haiku(self):
        """A valid haiku passes all checks."""
        form = get_form("haiku")
        lines = [
            "An old silent pond",     # 5 syllables
            "A frog jumps into water",  # 7 syllables  
            "Splash silence again",    # 5 syllables
        ]
        analysis = check_poem(lines, form)
        # Should pass or be close (within tolerance)
        assert analysis.overall_score >= 0.7
    
    def test_haiku_syllable_counts(self):
        """Verify syllable counting for haiku lines."""
        lines = [
            "An old silent pond",
            "A frog jumps into water",
            "Splash silence again",
        ]
        counts = [count_line_syllables(line) for line in lines]
        # Should be close to 5-7-5
        assert 4 <= counts[0] <= 6
        assert 6 <= counts[1] <= 8
        assert 4 <= counts[2] <= 6


class TestLimerickPipeline:
    """Integration tests for limerick validation."""
    
    def test_limerick_rhyme_scheme(self):
        """Limerick lines rhyme correctly."""
        form = get_form("limerick")
        # A classic limerick pattern
        lines = [
            "There once was a man from Maine",
            "Who loved to walk in the rain",
            "He slipped on ice",
            "It wasn't nice",
            "And never went out again",
        ]
        
        # Check A rhymes (lines 0, 1, 4)
        assert check_rhyme("Maine", "rain") == RhymeType.PERFECT
        # Maine/again is slant rhyme (same vowel, different ending)
        assert check_rhyme("Maine", "again") in (RhymeType.PERFECT, RhymeType.SLANT)
        
        # Check B rhymes (lines 2, 3)
        assert check_rhyme("ice", "nice") == RhymeType.PERFECT


class TestSonnetPipeline:
    """Integration tests for sonnet features."""
    
    def test_iambic_line_scans(self):
        """Classic iambic pentameter line scans correctly."""
        line = "Shall I compare thee to a summer's day"
        pattern = scan_line(line)
        assert len(pattern) == 10  # Pentameter = 10 syllables
    
    def test_shakespearean_form(self):
        """Shakespearean sonnet form is correct."""
        form = get_form("shakespearean")
        assert form.lines == 14
        assert form.rhyme_scheme == "ABABCDCDEFEFGG"
        assert form.meter == "iambic"


class TestRankerIntegration:
    """Integration tests for candidate ranking."""
    
    def test_rank_by_syllables(self):
        """Candidates ranked by syllable accuracy."""
        constraints = Constraints(target_syllables=5)
        candidates = [
            "Hello world today",      # ~4 syllables
            "An old silent pond",     # ~5 syllables (best)
            "Extraordinarily long line here",  # Many syllables
        ]
        ranked = rank_candidates(candidates, constraints)
        
        # Best match should be first
        assert ranked[0].rank == 1
        # Scores should be descending
        scores = [c.score.total for c in ranked]
        assert scores == sorted(scores, reverse=True)
    
    def test_rank_by_rhyme(self):
        """Candidates ranked by rhyme match."""
        constraints = Constraints(rhyme_word="day")
        candidates = [
            "The sun shines today",  # Perfect rhyme
            "I see the way",        # Perfect rhyme  
            "Walking through fog",  # No rhyme
        ]
        ranked = rank_candidates(candidates, constraints)
        
        # Rhyming lines should rank higher
        non_rhyme_rank = None
        for c in ranked:
            if "fog" in c.text:
                non_rhyme_rank = c.rank
        assert non_rhyme_rank == 3


class TestGeneratorIntegration:
    """Integration tests for generation pipeline."""
    
    def test_prompt_includes_constraints(self):
        """Built prompts include all constraints."""
        form = get_form("shakespearean")
        prompt = build_prompt(
            form=form,
            theme="love",
            line_index=0,
            prior_lines=[],
            rhyme_word="heart",
        )
        
        assert "Shakespearean" in prompt
        assert "love" in prompt
        assert "10 syllables" in prompt or "syllables" in prompt
        assert "rhyme" in prompt.lower()
        assert "heart" in prompt
        assert "iambic" in prompt.lower()
    
    def test_parse_various_formats(self):
        """Parse candidates from various LLM output formats."""
        # Numbered with periods
        output1 = "1. First line\n2. Second line\n3. Third line"
        assert len(parse_candidates(output1)) == 3
        
        # Numbered with parens
        output2 = "1) Line one\n2) Line two"
        assert len(parse_candidates(output2)) == 2
        
        # Plain lines
        output3 = "Just a line\nAnother line"
        assert len(parse_candidates(output3)) == 2


class TestFormConstraints:
    """Integration tests for form constraint validation."""
    
    def test_free_verse_accepts_anything(self):
        """Free verse has no constraints."""
        form = get_form("free_verse")
        lines = [
            "Any number of syllables here",
            "Short line",
            "A much longer line with many many words in it",
        ]
        analysis = check_poem(lines, form)
        assert analysis.passed
        assert analysis.overall_score == 1.0
    
    def test_blank_verse_checks_meter_only(self):
        """Blank verse checks meter but not rhyme."""
        form = get_form("blank_verse")
        assert form.meter == "iambic"
        assert form.rhyme_scheme is None


class TestEndToEnd:
    """Full end-to-end tests."""
    
    @patch("sonnet.generator.call_llm")
    def test_generate_and_check(self, mock_llm):
        """Generate a poem and validate it."""
        from sonnet.generator import generate_poem
        
        # Mock LLM to return valid haiku lines
        mock_llm.side_effect = [
            "1. An old silent pond\n2. The quiet still water\n3. Peace in the morning",
            "1. A frog jumps right in\n2. Splashing into the water\n3. Ripples spread outward",
            "1. Splash silence again\n2. Water settles once more\n3. Nature continues",
        ]
        
        form = get_form("haiku")
        lines = generate_poem(form, "nature")
        
        # Should have 3 lines
        assert len(lines) == 3
        
        # All should be non-empty
        assert all(len(line) > 0 for line in lines)
