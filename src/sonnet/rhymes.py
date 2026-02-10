"""Rhyme detection using phoneme matching."""

from enum import Enum
from typing import List, Optional, Tuple

from sonnet.syllables import get_phonemes, get_cmu_dict


class RhymeType(Enum):
    """Types of rhyme."""
    PERFECT = "perfect"
    SLANT = "slant"
    NONE = "none"


# Vowel phonemes (those that carry stress markers)
VOWEL_PHONEMES = {
    "AA", "AE", "AH", "AO", "AW", "AY", 
    "EH", "ER", "EY", "IH", "IY", 
    "OW", "OY", "UH", "UW"
}


def _strip_stress(phoneme: str) -> str:
    """Remove stress marker from phoneme."""
    if phoneme and phoneme[-1].isdigit():
        return phoneme[:-1]
    return phoneme


def _is_vowel(phoneme: str) -> bool:
    """Check if phoneme is a vowel."""
    base = _strip_stress(phoneme)
    return base in VOWEL_PHONEMES


def get_rhyme_phonemes(word: str) -> Optional[List[str]]:
    """
    Get the phonemes from the last stressed vowel to end of word.
    
    This is the part that determines rhyme.
    Returns None if word not in dictionary.
    """
    phonemes = get_phonemes(word)
    if phonemes is None:
        return None
    
    # Find the last stressed vowel (stress = 1 or 2)
    last_stressed_idx = -1
    for i, p in enumerate(phonemes):
        if p[-1] in "12":  # Primary or secondary stress
            last_stressed_idx = i
    
    # If no stressed vowel found, use last vowel
    if last_stressed_idx == -1:
        for i, p in enumerate(phonemes):
            if _is_vowel(p):
                last_stressed_idx = i
    
    if last_stressed_idx == -1:
        return None
    
    return phonemes[last_stressed_idx:]


def check_rhyme(word1: str, word2: str) -> RhymeType:
    """
    Check if two words rhyme.
    
    Returns:
        RhymeType.PERFECT: Exact match of rhyme phonemes
        RhymeType.SLANT: Vowels match but consonants may differ
        RhymeType.NONE: No rhyme detected
    """
    # Same word rhymes with itself
    if word1.lower().strip() == word2.lower().strip():
        return RhymeType.PERFECT
    
    rhyme1 = get_rhyme_phonemes(word1)
    rhyme2 = get_rhyme_phonemes(word2)
    
    if rhyme1 is None or rhyme2 is None:
        return RhymeType.NONE
    
    # Strip stress for comparison
    stripped1 = [_strip_stress(p) for p in rhyme1]
    stripped2 = [_strip_stress(p) for p in rhyme2]
    
    # Perfect rhyme: exact match of rhyme portion
    if stripped1 == stripped2:
        return RhymeType.PERFECT
    
    # Slant rhyme: vowels match, consonants may differ
    vowels1 = [p for p in stripped1 if p in VOWEL_PHONEMES]
    vowels2 = [p for p in stripped2 if p in VOWEL_PHONEMES]
    
    if vowels1 and vowels2 and vowels1 == vowels2:
        return RhymeType.SLANT
    
    # Check for near-rhyme (last vowel and final consonant similar)
    if len(stripped1) >= 1 and len(stripped2) >= 1:
        if stripped1[-1] == stripped2[-1]:
            return RhymeType.SLANT
    
    return RhymeType.NONE


def find_rhymes(
    word: str, 
    candidates: List[str], 
    include_slant: bool = True
) -> List[Tuple[str, RhymeType]]:
    """
    Find words that rhyme with the given word from a list of candidates.
    
    Returns list of (word, rhyme_type) tuples, sorted by quality (perfect first).
    """
    if not word or not candidates:
        return []
    
    results = []
    for candidate in candidates:
        rhyme_type = check_rhyme(word, candidate)
        if rhyme_type == RhymeType.PERFECT:
            results.append((candidate, rhyme_type))
        elif include_slant and rhyme_type == RhymeType.SLANT:
            results.append((candidate, rhyme_type))
    
    # Sort: perfect rhymes first
    results.sort(key=lambda x: 0 if x[1] == RhymeType.PERFECT else 1)
    
    return results


def get_last_word(line: str) -> str:
    """Extract the last word from a line (for rhyme checking)."""
    import re
    words = re.findall(r"[a-zA-Z'-]+", line)
    return words[-1] if words else ""


def get_rhyme_groups(scheme: str) -> dict:
    """
    Parse a rhyme scheme string into groups.
    
    E.g., "ABAB" -> {"A": [0, 2], "B": [1, 3]}
    """
    groups = {}
    for i, letter in enumerate(scheme.upper()):
        if letter.isalpha():
            if letter not in groups:
                groups[letter] = []
            groups[letter].append(i)
    return groups


def suggest_rhymes(
    word: str,
    max_results: int = 20,
    min_syllables: Optional[int] = None,
    max_syllables: Optional[int] = None,
    include_slant: bool = True,
) -> List[Tuple[str, RhymeType, int]]:
    """
    Suggest rhyming words from the CMU dictionary.
    
    Args:
        word: The word to find rhymes for
        max_results: Maximum number of results to return
        min_syllables: Minimum syllable count filter (optional)
        max_syllables: Maximum syllable count filter (optional)
        include_slant: Whether to include slant rhymes
        
    Returns:
        List of (word, rhyme_type, syllable_count) tuples, sorted by quality
    """
    from sonnet.syllables import count_syllables
    
    cmu = get_cmu_dict()
    if not cmu:
        return []
    
    target_rhyme = get_rhyme_phonemes(word)
    if target_rhyme is None:
        return []
    
    target_stripped = [_strip_stress(p) for p in target_rhyme]
    target_vowels = [p for p in target_stripped if p in VOWEL_PHONEMES]
    
    results = []
    word_lower = word.lower().strip()
    
    for candidate in cmu.keys():
        # Skip the word itself
        if candidate.lower() == word_lower:
            continue
        
        # Skip words with numbers or special chars
        if not candidate.isalpha():
            continue
        
        candidate_rhyme = get_rhyme_phonemes(candidate)
        if candidate_rhyme is None:
            continue
        
        candidate_stripped = [_strip_stress(p) for p in candidate_rhyme]
        
        # Check for perfect rhyme
        if candidate_stripped == target_stripped:
            syllables = count_syllables(candidate)
            
            # Apply syllable filters
            if min_syllables and syllables < min_syllables:
                continue
            if max_syllables and syllables > max_syllables:
                continue
                
            results.append((candidate, RhymeType.PERFECT, syllables))
            continue
        
        # Check for slant rhyme if enabled
        if include_slant:
            candidate_vowels = [p for p in candidate_stripped if p in VOWEL_PHONEMES]
            
            is_slant = False
            # Vowels match
            if target_vowels and candidate_vowels and target_vowels == candidate_vowels:
                is_slant = True
            # Last consonant matches
            elif len(target_stripped) >= 1 and len(candidate_stripped) >= 1:
                if target_stripped[-1] == candidate_stripped[-1]:
                    is_slant = True
            
            if is_slant:
                syllables = count_syllables(candidate)
                if min_syllables and syllables < min_syllables:
                    continue
                if max_syllables and syllables > max_syllables:
                    continue
                results.append((candidate, RhymeType.SLANT, syllables))
    
    # Sort: perfect first, then by syllable count, then alphabetically
    results.sort(key=lambda x: (
        0 if x[1] == RhymeType.PERFECT else 1,
        x[2],  # syllable count
        x[0],  # alphabetically
    ))
    
    return results[:max_results]
