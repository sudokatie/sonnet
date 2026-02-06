"""Syllable counting using CMU Pronouncing Dictionary and heuristics."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Module-level cache for CMU dictionary
_CMU_DICT: Optional[Dict[str, List[List[str]]]] = None


def _get_data_path() -> Path:
    """Get path to data directory."""
    # Try relative to this file first
    pkg_dir = Path(__file__).parent.parent.parent
    data_path = pkg_dir / "data" / "cmudict.txt"
    if data_path.exists():
        return data_path
    
    # Try installed package location
    import importlib.resources as pkg_resources
    try:
        with pkg_resources.files("sonnet").joinpath("data/cmudict.txt") as p:
            if p.exists():
                return Path(p)
    except (AttributeError, TypeError):
        pass
    
    # Fallback to current directory
    return Path("data/cmudict.txt")


def _load_cmu_dict() -> Dict[str, List[List[str]]]:
    """
    Load and parse CMU Pronouncing Dictionary.
    
    Returns dict mapping lowercase word to list of pronunciations,
    where each pronunciation is a list of phonemes.
    """
    result: Dict[str, List[List[str]]] = {}
    data_path = _get_data_path()
    
    if not data_path.exists():
        return result
    
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";;;"):
                continue
            
            parts = line.split()
            if len(parts) < 2:
                continue
            
            word = parts[0].lower()
            phonemes = parts[1:]
            
            # Handle alternate pronunciations: word(2), word(3), etc.
            # Strip the (N) suffix to get base word
            base_word = re.sub(r"\(\d+\)$", "", word)
            
            if base_word not in result:
                result[base_word] = []
            result[base_word].append(phonemes)
    
    return result


def get_cmu_dict() -> Dict[str, List[List[str]]]:
    """Get CMU dictionary, loading if necessary (cached)."""
    global _CMU_DICT
    if _CMU_DICT is None:
        _CMU_DICT = _load_cmu_dict()
    return _CMU_DICT


def get_phonemes(word: str) -> Optional[List[str]]:
    """
    Get phonemes for a word from CMU dictionary.
    
    Returns first pronunciation if multiple exist, or None if not found.
    """
    cmu = get_cmu_dict()
    clean_word = re.sub(r"[^\w'-]", "", word.lower())
    
    if clean_word in cmu:
        return cmu[clean_word][0]
    return None


def count_syllables_cmu(word: str) -> Optional[int]:
    """
    Count syllables using CMU dictionary.
    
    Syllables are counted by finding phonemes with stress markers (0, 1, 2).
    Returns None if word not in dictionary.
    """
    phonemes = get_phonemes(word)
    if phonemes is None:
        return None
    
    # Count phonemes that end with a digit (stress marker = vowel)
    count = sum(1 for p in phonemes if p[-1].isdigit())
    return count


def _heuristic_count(word: str) -> int:
    """
    Count syllables using heuristic rules (fallback for unknown words).
    
    Rules:
    1. Count vowel groups (consecutive vowels = 1)
    2. Subtract for silent-e at end
    3. Handle common suffixes
    4. Minimum 1 syllable
    """
    word = word.lower().strip()
    word = re.sub(r"[^a-z]", "", word)
    
    if not word:
        return 0
    
    # Vowels
    vowels = "aeiouy"
    
    # Count vowel groups
    count = 0
    prev_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    
    # Subtract for silent-e at end (but not "le" endings like "able")
    if word.endswith("e") and len(word) > 2:
        if not word.endswith("le") or word[-3] not in vowels:
            count -= 1
    
    # Handle -ed endings (usually not a syllable unless preceded by t or d)
    if word.endswith("ed") and len(word) > 2:
        if word[-3] not in "td":
            count -= 1
    
    # Handle -es endings
    if word.endswith("es") and len(word) > 2:
        if word[-3] in "sxz" or word.endswith("shes") or word.endswith("ches"):
            pass  # Keep the syllable
        else:
            count -= 1
    
    # Minimum 1 syllable
    return max(1, count)


def count_syllables(word: str) -> int:
    """
    Count syllables in a word.
    
    Uses CMU dictionary if available, falls back to heuristic.
    """
    if not word or not word.strip():
        return 0
    
    # Try CMU first
    cmu_count = count_syllables_cmu(word)
    if cmu_count is not None:
        return cmu_count
    
    # Fall back to heuristic
    return _heuristic_count(word)


def count_syllables_detailed(word: str) -> Tuple[int, str]:
    """
    Count syllables with source information.
    
    Returns (count, source) where source is "cmu" or "heuristic".
    """
    if not word or not word.strip():
        return (0, "empty")
    
    cmu_count = count_syllables_cmu(word)
    if cmu_count is not None:
        return (cmu_count, "cmu")
    
    return (_heuristic_count(word), "heuristic")


def count_line_syllables(line: str) -> int:
    """Count total syllables in a line of text."""
    if not line:
        return 0
    
    # Split on whitespace and punctuation, keep only words
    words = re.findall(r"[a-zA-Z'-]+", line)
    return sum(count_syllables(w) for w in words)
