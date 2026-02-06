"""
Poetic form definitions.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, List, Dict


@dataclass
class FormDefinition:
    """Definition of a poetic form with constraints."""
    name: str
    lines: int
    syllables: Union[List[int], int]  # Per-line list or uniform count
    rhyme_scheme: Optional[str]       # e.g., "ABAB" or None
    meter: Optional[str]              # "iambic", "trochaic", etc.
    description: str


FORMS: Dict[str, FormDefinition] = {
    "haiku": FormDefinition(
        name="Haiku",
        lines=3,
        syllables=[5, 7, 5],
        rhyme_scheme=None,
        meter=None,
        description="Japanese 5-7-5 syllable poem"
    ),
    "limerick": FormDefinition(
        name="Limerick",
        lines=5,
        syllables=[8, 8, 5, 5, 8],  # 8-9, 8-9, 5-6, 5-6, 8-9 (using midpoint)
        rhyme_scheme="AABBA",
        meter="anapestic",
        description="Humorous 5-line poem with AABBA rhyme"
    ),
    "shakespearean": FormDefinition(
        name="Shakespearean Sonnet",
        lines=14,
        syllables=10,  # Uniform iambic pentameter
        rhyme_scheme="ABABCDCDEFEFGG",
        meter="iambic",
        description="14-line sonnet with three quatrains and a couplet"
    ),
    "blank_verse": FormDefinition(
        name="Blank Verse",
        lines=14,  # Default, can vary
        syllables=10,  # Iambic pentameter
        rhyme_scheme=None,
        meter="iambic",
        description="Unrhymed iambic pentameter"
    ),
    "free_verse": FormDefinition(
        name="Free Verse",
        lines=10,  # Default, user can override
        syllables=0,  # No constraint
        rhyme_scheme=None,
        meter=None,
        description="No fixed constraints on meter or rhyme"
    ),
}


def get_form(name: str) -> FormDefinition:
    """
    Get a form definition by name.
    
    Args:
        name: Form name (case-insensitive, underscores/hyphens normalized)
    
    Returns:
        FormDefinition for the requested form
    
    Raises:
        ValueError: If form name not found
    """
    normalized = name.lower().replace("-", "_").replace(" ", "_")
    if normalized in FORMS:
        return FORMS[normalized]
    raise ValueError(f"Unknown form: {name}. Available: {', '.join(FORMS.keys())}")


def list_forms() -> List[str]:
    """
    Get list of available form names.
    
    Returns:
        List of form names (lowercase with underscores)
    """
    return list(FORMS.keys())


def get_rhyme_groups(scheme: str) -> Dict[str, List[int]]:
    """
    Parse a rhyme scheme into groups of line indices that should rhyme.
    
    Args:
        scheme: Rhyme scheme string, e.g., "ABAB" or "AABBA"
    
    Returns:
        Dict mapping rhyme letter to list of 0-indexed line positions
        
    Example:
        >>> get_rhyme_groups("ABAB")
        {'A': [0, 2], 'B': [1, 3]}
        >>> get_rhyme_groups("AABBA")
        {'A': [0, 1, 4], 'B': [2, 3]}
    """
    groups: Dict[str, List[int]] = {}
    for i, letter in enumerate(scheme.upper()):
        if letter not in groups:
            groups[letter] = []
        groups[letter].append(i)
    return groups


def get_syllable_target(form: FormDefinition, line_index: int) -> int:
    """
    Get the target syllable count for a specific line.
    
    Args:
        form: The form definition
        line_index: 0-indexed line number
    
    Returns:
        Target syllable count (0 means no constraint)
    """
    if isinstance(form.syllables, int):
        return form.syllables
    if 0 <= line_index < len(form.syllables):
        return form.syllables[line_index]
    return 0
