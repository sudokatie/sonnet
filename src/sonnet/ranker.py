"""
Candidate ranking by constraint satisfaction.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from sonnet.syllables import count_line_syllables
from sonnet.rhymes import check_rhyme, RhymeType
from sonnet.meter import match_meter, MeterType


@dataclass
class RankingScore:
    """Breakdown of constraint scores for a candidate."""
    syllable_score: float = 1.0  # 0-1
    rhyme_score: float = 1.0    # 0-1
    meter_score: float = 1.0    # 0-1
    
    @property
    def total(self) -> float:
        """Weighted total score."""
        weights = {"syllable": 0.4, "rhyme": 0.35, "meter": 0.25}
        return (
            self.syllable_score * weights["syllable"] +
            self.rhyme_score * weights["rhyme"] +
            self.meter_score * weights["meter"]
        )


@dataclass
class RankedCandidate:
    """A candidate with its ranking score."""
    text: str
    score: RankingScore
    rank: int = 0


@dataclass
class Constraints:
    """Constraints for ranking candidates."""
    target_syllables: int = 0      # 0 = no constraint
    rhyme_word: Optional[str] = None
    meter: Optional[str] = None    # "iambic", "trochaic", etc.
    expected_syllables: int = 10   # For meter matching


def _meter_type_from_string(meter: str) -> Optional[MeterType]:
    """Convert meter string to MeterType enum."""
    mapping = {
        "iambic": MeterType.IAMBIC,
        "trochaic": MeterType.TROCHAIC,
        "anapestic": MeterType.ANAPESTIC,
        "dactylic": MeterType.DACTYLIC,
        "spondaic": MeterType.SPONDAIC,
    }
    return mapping.get(meter.lower()) if meter else None


def score_syllables(text: str, target: int, tolerance: int = 1) -> float:
    """
    Score a line based on syllable count.
    
    Args:
        text: The line of text
        target: Target syllable count (0 = no constraint)
        tolerance: Allowed deviation (default 1)
    
    Returns:
        Score from 0.0 to 1.0
    """
    if target == 0:
        return 1.0
    
    actual = count_line_syllables(text)
    diff = abs(actual - target)
    
    if diff <= tolerance:
        # Within tolerance: 1.0 for exact, 0.9 for 1 off
        return 1.0 - (diff * 0.1)
    else:
        # Beyond tolerance: decrease by 0.2 per syllable
        return max(0.0, 0.8 - ((diff - tolerance) * 0.2))


def score_rhyme(text: str, rhyme_word: Optional[str]) -> float:
    """
    Score a line based on rhyme with target word.
    
    Args:
        text: The line of text
        rhyme_word: Word that line should rhyme with
    
    Returns:
        Score from 0.0 to 1.0
    """
    if not rhyme_word:
        return 1.0
    
    # Get last word of line
    words = text.split()
    if not words:
        return 0.0
    
    last_word = words[-1].strip(".,!?;:'\"")
    rhyme_type = check_rhyme(last_word, rhyme_word)
    
    if rhyme_type == RhymeType.PERFECT:
        return 1.0
    elif rhyme_type == RhymeType.SLANT:
        return 0.7
    else:
        return 0.0


def score_meter(
    text: str, 
    meter: Optional[str], 
    expected_syllables: int = 10
) -> float:
    """
    Score a line based on meter pattern.
    
    Args:
        text: The line of text
        meter: Meter type (e.g., "iambic")
        expected_syllables: Expected syllable count for pattern
    
    Returns:
        Score from 0.0 to 1.0
    """
    if not meter:
        return 1.0
    
    meter_type = _meter_type_from_string(meter)
    if not meter_type:
        return 1.0
    
    return match_meter(text, meter_type, expected_syllables)


def score_candidate(
    text: str, 
    constraints: Constraints,
) -> RankingScore:
    """
    Score a candidate line against all constraints.
    
    Args:
        text: The candidate line
        constraints: Constraint requirements
    
    Returns:
        RankingScore with breakdown
    """
    return RankingScore(
        syllable_score=score_syllables(text, constraints.target_syllables),
        rhyme_score=score_rhyme(text, constraints.rhyme_word),
        meter_score=score_meter(
            text, 
            constraints.meter, 
            constraints.expected_syllables
        ),
    )


def rank_candidates(
    candidates: List[str],
    constraints: Constraints,
) -> List[RankedCandidate]:
    """
    Rank a list of candidates by constraint satisfaction.
    
    Args:
        candidates: List of candidate lines
        constraints: Constraint requirements
    
    Returns:
        List of RankedCandidate sorted by score (best first)
    """
    scored = []
    for text in candidates:
        score = score_candidate(text, constraints)
        scored.append(RankedCandidate(text=text, score=score))
    
    # Sort by total score, descending
    scored.sort(key=lambda c: c.score.total, reverse=True)
    
    # Assign ranks
    for i, candidate in enumerate(scored):
        candidate.rank = i + 1
    
    return scored


def get_best_candidate(
    candidates: List[str],
    constraints: Constraints,
) -> Optional[RankedCandidate]:
    """
    Get the best scoring candidate.
    
    Args:
        candidates: List of candidate lines
        constraints: Constraint requirements
    
    Returns:
        Best RankedCandidate or None if no candidates
    """
    ranked = rank_candidates(candidates, constraints)
    return ranked[0] if ranked else None
