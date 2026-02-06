"""Meter scanning and pattern matching."""

import re
from enum import Enum
from typing import List, Optional

from sonnet.syllables import get_phonemes, count_syllables


class MeterType(Enum):
    """Types of poetic meter."""
    IAMBIC = "iambic"        # da-DUM (u/)
    TROCHAIC = "trochaic"    # DUM-da (/u)
    ANAPESTIC = "anapestic"  # da-da-DUM (uu/)
    DACTYLIC = "dactylic"    # DUM-da-da (/uu)
    SPONDAIC = "spondaic"    # DUM-DUM (//)


# Meter patterns (u = unstressed, / = stressed)
METER_PATTERNS = {
    MeterType.IAMBIC: "u/",
    MeterType.TROCHAIC: "/u",
    MeterType.ANAPESTIC: "uu/",
    MeterType.DACTYLIC: "/uu",
    MeterType.SPONDAIC: "//",
}


def get_word_stress(word: str) -> str:
    """
    Get stress pattern for a word.
    
    Returns string of 'u' (unstressed) and '/' (stressed).
    Uses CMU dictionary if available, else heuristic.
    """
    phonemes = get_phonemes(word)
    
    if phonemes:
        pattern = ""
        for p in phonemes:
            if p[-1].isdigit():
                stress = int(p[-1])
                if stress == 0:
                    pattern += "u"
                else:
                    pattern += "/"
        return pattern if pattern else "u"
    
    # Heuristic fallback: alternate u/ starting with u
    syllables = count_syllables(word)
    if syllables <= 1:
        return "u"  # Single syllable words are often unstressed
    
    # Common pattern: stress on first syllable for 2-syllable words
    pattern = ""
    for i in range(syllables):
        if i == 0:
            pattern += "/"  # First syllable stressed (common in English)
        else:
            pattern += "u"
    return pattern


def scan_line(line: str) -> str:
    """
    Scan a line of poetry for its stress pattern.
    
    Returns string of 'u' (unstressed) and '/' (stressed).
    """
    if not line:
        return ""
    
    # Extract words
    words = re.findall(r"[a-zA-Z'-]+", line)
    
    pattern = ""
    for word in words:
        word_pattern = get_word_stress(word)
        pattern += word_pattern
    
    return pattern


def get_expected_pattern(meter: MeterType, syllables: int) -> str:
    """
    Generate expected stress pattern for a given meter and syllable count.
    
    For iambic pentameter (10 syllables): u/u/u/u/u/
    """
    base = METER_PATTERNS[meter]
    base_len = len(base)
    
    # Repeat pattern to fill syllable count
    repeats = (syllables + base_len - 1) // base_len
    full_pattern = base * repeats
    
    return full_pattern[:syllables]


def _pattern_similarity(actual: str, expected: str) -> float:
    """
    Calculate similarity between two stress patterns.
    
    Returns 0-1 score.
    """
    if not actual or not expected:
        return 0.0
    
    # Pad shorter pattern
    max_len = max(len(actual), len(expected))
    actual = actual.ljust(max_len, "u")
    expected = expected.ljust(max_len, "u")
    
    # Count matches
    matches = sum(1 for a, e in zip(actual, expected) if a == e)
    return matches / max_len


def match_meter(
    line: str, 
    meter: MeterType, 
    expected_syllables: Optional[int] = None
) -> float:
    """
    Check how well a line matches a given meter.
    
    Returns score from 0.0 (no match) to 1.0 (perfect match).
    """
    actual = scan_line(line)
    
    if not actual:
        return 0.0
    
    # If expected syllables specified, use that for pattern
    if expected_syllables:
        expected = get_expected_pattern(meter, expected_syllables)
    else:
        expected = get_expected_pattern(meter, len(actual))
    
    return _pattern_similarity(actual, expected)


def describe_meter(meter: MeterType, feet: int = 5) -> str:
    """
    Get human-readable description of a meter.
    
    E.g., iambic pentameter (5 feet) = 10 syllables.
    """
    names = {
        1: "monometer",
        2: "dimeter",
        3: "trimeter",
        4: "tetrameter",
        5: "pentameter",
        6: "hexameter",
        7: "heptameter",
        8: "octameter",
    }
    
    foot_name = names.get(feet, f"{feet}-meter")
    return f"{meter.value} {foot_name}"
