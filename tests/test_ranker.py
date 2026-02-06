"""
Tests for ranker.py - candidate scoring and ranking.
"""

import pytest
from sonnet.ranker import (
    RankingScore,
    RankedCandidate,
    Constraints,
    score_syllables,
    score_rhyme,
    score_meter,
    score_candidate,
    rank_candidates,
    get_best_candidate,
)


class TestRankingScore:
    """Tests for RankingScore dataclass."""
    
    def test_perfect_score(self):
        """Perfect scores give 1.0 total."""
        score = RankingScore(
            syllable_score=1.0,
            rhyme_score=1.0,
            meter_score=1.0,
        )
        assert score.total == 1.0
    
    def test_zero_scores(self):
        """Zero scores give 0.0 total."""
        score = RankingScore(
            syllable_score=0.0,
            rhyme_score=0.0,
            meter_score=0.0,
        )
        assert score.total == 0.0
    
    def test_weighted_total(self):
        """Weights are applied correctly."""
        # syllable=0.4, rhyme=0.35, meter=0.25
        score = RankingScore(
            syllable_score=1.0,
            rhyme_score=0.0,
            meter_score=0.0,
        )
        assert abs(score.total - 0.4) < 0.01


class TestScoreSyllables:
    """Tests for syllable scoring."""
    
    def test_exact_match(self):
        """Exact syllable count scores 1.0."""
        # "hello world" = 3 syllables
        score = score_syllables("hello world", target=3)
        assert score == 1.0
    
    def test_one_off(self):
        """One syllable off scores 0.9."""
        score = score_syllables("hello", target=3)  # 2 syllables
        assert score == 0.9
    
    def test_no_constraint(self):
        """Target of 0 means no constraint (1.0)."""
        score = score_syllables("anything here", target=0)
        assert score == 1.0
    
    def test_way_off(self):
        """Many syllables off scores low."""
        score = score_syllables("hi", target=10)  # 1 vs 10
        assert score < 0.5


class TestScoreRhyme:
    """Tests for rhyme scoring."""
    
    def test_perfect_rhyme(self):
        """Perfect rhyme scores 1.0."""
        score = score_rhyme("I love to play in the rain", "Maine")
        assert score == 1.0
    
    def test_slant_rhyme(self):
        """Slant rhyme scores 0.7."""
        # time/mine are slant rhymes (same vowel, diff consonant)
        score = score_rhyme("I ran out of time", "mine")
        assert abs(score - 0.7) < 0.01
    
    def test_no_rhyme(self):
        """No rhyme scores 0.0."""
        score = score_rhyme("I love the dog", "rain")
        assert score == 0.0
    
    def test_no_constraint(self):
        """No rhyme word means no constraint (1.0)."""
        score = score_rhyme("anything here", None)
        assert score == 1.0


class TestScoreMeter:
    """Tests for meter scoring."""
    
    def test_no_constraint(self):
        """No meter constraint scores 1.0."""
        score = score_meter("anything here", None)
        assert score == 1.0
    
    def test_iambic_line(self):
        """Iambic meter scores based on match."""
        # Classic iambic line
        score = score_meter(
            "Shall I compare thee to a summer's day",
            "iambic",
            expected_syllables=10
        )
        assert score > 0.4  # Should score reasonably well


class TestScoreCandidate:
    """Tests for full candidate scoring."""
    
    def test_no_constraints(self):
        """No constraints gives perfect score."""
        constraints = Constraints()
        score = score_candidate("any text here", constraints)
        assert score.total == 1.0
    
    def test_syllable_constraint(self):
        """Syllable constraint applied."""
        constraints = Constraints(target_syllables=5)
        score = score_candidate("hello world today", constraints)
        # Should be close to target
        assert score.syllable_score >= 0.8


class TestRankCandidates:
    """Tests for ranking multiple candidates."""
    
    def test_ranks_by_score(self):
        """Candidates ranked by total score."""
        constraints = Constraints(target_syllables=5, rhyme_word="day")
        candidates = [
            "I saw the sun today",  # 5 syllables, rhymes
            "Extraordinary magnificent day",  # Wrong syllables
            "The cat sat on a log",  # 5 syllables, no rhyme
        ]
        ranked = rank_candidates(candidates, constraints)
        
        # First should rhyme and have right syllables
        assert ranked[0].rank == 1
        assert "today" in ranked[0].text or "day" in ranked[0].text
    
    def test_assigns_ranks(self):
        """Ranks are 1-indexed."""
        constraints = Constraints()
        candidates = ["one", "two", "three"]
        ranked = rank_candidates(candidates, constraints)
        
        assert [c.rank for c in ranked] == [1, 2, 3]
    
    def test_empty_candidates(self):
        """Empty list returns empty."""
        ranked = rank_candidates([], Constraints())
        assert len(ranked) == 0


class TestGetBestCandidate:
    """Tests for getting best candidate."""
    
    def test_returns_best(self):
        """Returns highest scoring candidate."""
        constraints = Constraints(target_syllables=5, rhyme_word="night")
        candidates = [
            "I love the dark of night",
            "The sun is very bright",
            "Random words here now",
        ]
        best = get_best_candidate(candidates, constraints)
        
        assert best is not None
        assert best.rank == 1
    
    def test_empty_returns_none(self):
        """Empty list returns None."""
        best = get_best_candidate([], Constraints())
        assert best is None
