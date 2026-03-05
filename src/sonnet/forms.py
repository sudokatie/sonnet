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


# Sestina end-word rotation pattern
# Each stanza uses the same 6 words as line endings, but in a rotating order
# Pattern: line endings go to positions (6,1,5,2,4,3) -> previous stanza's order
SESTINA_ROTATION = [
    [1, 2, 3, 4, 5, 6],  # Stanza 1: original order
    [6, 1, 5, 2, 4, 3],  # Stanza 2
    [3, 6, 4, 1, 2, 5],  # Stanza 3
    [5, 3, 2, 6, 1, 4],  # Stanza 4
    [4, 5, 1, 3, 6, 2],  # Stanza 5
    [2, 4, 6, 5, 3, 1],  # Stanza 6
]

# Envoi typically uses words in middle/end positions: (2,5) (4,3) (6,1)
SESTINA_ENVOI = [(2, 5), (4, 3), (6, 1)]


def get_sestina_end_word_order(stanza: int) -> List[int]:
    """
    Get the end-word order for a specific sestina stanza (0-indexed).
    
    Args:
        stanza: Stanza number (0-5)
    
    Returns:
        List of 1-indexed word positions for that stanza's line endings
    """
    if 0 <= stanza < 6:
        return SESTINA_ROTATION[stanza]
    raise ValueError(f"Sestina stanza must be 0-5, got {stanza}")


def get_sestina_line_end_word(line_index: int) -> int:
    """
    Get which end-word (1-6) should be used for a specific line of a sestina.
    
    Args:
        line_index: 0-indexed line number (0-35 for main stanzas, 36-38 for envoi)
    
    Returns:
        1-indexed end-word number, or 0 if line is in envoi (special handling)
    """
    if line_index < 36:
        stanza = line_index // 6
        line_in_stanza = line_index % 6
        return SESTINA_ROTATION[stanza][line_in_stanza]
    # Envoi lines (36-38) need special handling - two words per line
    return 0


FORMS: Dict[str, FormDefinition] = {
    "haiku": FormDefinition(
        name="Haiku",
        lines=3,
        syllables=[5, 7, 5],
        rhyme_scheme=None,
        meter=None,
        description="Japanese 5-7-5 syllable poem"
    ),
    "tanka": FormDefinition(
        name="Tanka",
        lines=5,
        syllables=[5, 7, 5, 7, 7],
        rhyme_scheme=None,
        meter=None,
        description="Japanese 5-7-5-7-7 syllable poem, extending haiku"
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
    "villanelle": FormDefinition(
        name="Villanelle",
        lines=19,
        syllables=10,  # Typically iambic pentameter
        rhyme_scheme="ABA ABA ABA ABA ABA ABAA",  # A1bA2 abA1 abA2 abA1 abA2 abA1A2
        meter="iambic",
        description="19-line poem with two repeating refrains and ABA tercets"
    ),
    "ghazal": FormDefinition(
        name="Ghazal",
        lines=10,  # 5 couplets (typically 5-15 couplets)
        syllables=0,  # Varies, but lines should be similar length
        rhyme_scheme="AA BA CA DA EA",  # Each couplet's second line rhymes
        meter=None,
        description="Couplets with rhyming second lines and a refrain (radif)"
    ),
    "pantoum": FormDefinition(
        name="Pantoum",
        lines=16,  # Can vary, must be multiple of 4
        syllables=10,  # Often iambic pentameter
        rhyme_scheme="ABAB",  # Pattern repeats; lines 2,4 become 1,3 of next stanza
        meter="iambic",
        description="Interlocking quatrains with repeating lines"
    ),
    "sestina": FormDefinition(
        name="Sestina",
        lines=39,  # 6 stanzas of 6 lines + 3-line envoi
        syllables=10,  # Typically iambic pentameter
        rhyme_scheme=None,  # No traditional rhyme; uses end-word repetition instead
        meter="iambic",
        description="39-line poem with 6 end-words rotating through 6 stanzas plus envoi"
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
