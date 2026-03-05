"""
Tests for forms.py - poetic form definitions.
"""

import pytest
from sonnet.forms import (
    FormDefinition,
    FORMS,
    get_form,
    list_forms,
    get_rhyme_groups,
    get_syllable_target,
    SESTINA_ROTATION,
    SESTINA_ENVOI,
    get_sestina_end_word_order,
    get_sestina_line_end_word,
)


class TestFormDefinition:
    """Tests for FormDefinition dataclass."""
    
    def test_haiku_structure(self):
        """Haiku has correct structure."""
        haiku = FORMS["haiku"]
        assert haiku.name == "Haiku"
        assert haiku.lines == 3
        assert haiku.syllables == [5, 7, 5]
        assert haiku.rhyme_scheme is None
        assert haiku.meter is None
    
    def test_limerick_structure(self):
        """Limerick has AABBA rhyme scheme."""
        limerick = FORMS["limerick"]
        assert limerick.lines == 5
        assert limerick.rhyme_scheme == "AABBA"
        assert limerick.meter == "anapestic"
    
    def test_shakespearean_structure(self):
        """Shakespearean sonnet has 14 lines, iambic pentameter."""
        sonnet = FORMS["shakespearean"]
        assert sonnet.lines == 14
        assert sonnet.syllables == 10  # Uniform
        assert sonnet.rhyme_scheme == "ABABCDCDEFEFGG"
        assert sonnet.meter == "iambic"
    
    def test_blank_verse_no_rhyme(self):
        """Blank verse has meter but no rhyme."""
        bv = FORMS["blank_verse"]
        assert bv.rhyme_scheme is None
        assert bv.meter == "iambic"
    
    def test_free_verse_no_constraints(self):
        """Free verse has no meter or rhyme constraints."""
        fv = FORMS["free_verse"]
        assert fv.syllables == 0
        assert fv.rhyme_scheme is None
        assert fv.meter is None
    
    def test_tanka_structure(self):
        """Tanka extends haiku with 5-7-5-7-7 syllables."""
        tanka = FORMS["tanka"]
        assert tanka.name == "Tanka"
        assert tanka.lines == 5
        assert tanka.syllables == [5, 7, 5, 7, 7]
        assert tanka.rhyme_scheme is None
        assert tanka.meter is None
    
    def test_villanelle_structure(self):
        """Villanelle has 19 lines with repeating refrains."""
        villanelle = FORMS["villanelle"]
        assert villanelle.name == "Villanelle"
        assert villanelle.lines == 19
        assert villanelle.syllables == 10
        assert villanelle.meter == "iambic"
        # Has complex ABA pattern
        assert "ABA" in villanelle.rhyme_scheme
    
    def test_ghazal_structure(self):
        """Ghazal has couplets with rhyming second lines."""
        ghazal = FORMS["ghazal"]
        assert ghazal.name == "Ghazal"
        assert ghazal.lines == 10  # 5 couplets
        # Second lines of each couplet rhyme (AA, BA, CA, etc.)
        assert "AA" in ghazal.rhyme_scheme
    
    def test_pantoum_structure(self):
        """Pantoum has interlocking quatrains."""
        pantoum = FORMS["pantoum"]
        assert pantoum.name == "Pantoum"
        assert pantoum.lines == 16  # 4 quatrains
        assert pantoum.syllables == 10
        assert pantoum.meter == "iambic"


class TestGetForm:
    """Tests for get_form function."""
    
    def test_get_haiku(self):
        """Get haiku by name."""
        form = get_form("haiku")
        assert form.name == "Haiku"
    
    def test_case_insensitive(self):
        """Form lookup is case-insensitive."""
        assert get_form("HAIKU").name == "Haiku"
        assert get_form("Haiku").name == "Haiku"
        assert get_form("HaIkU").name == "Haiku"
    
    def test_hyphen_normalized(self):
        """Hyphens normalized to underscores."""
        assert get_form("blank-verse").name == "Blank Verse"
    
    def test_space_normalized(self):
        """Spaces normalized to underscores."""
        assert get_form("blank verse").name == "Blank Verse"
    
    def test_unknown_form_raises(self):
        """Unknown form raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_form("nonexistent")
        assert "Unknown form: nonexistent" in str(exc_info.value)


class TestListForms:
    """Tests for list_forms function."""
    
    def test_returns_all_forms(self):
        """Returns all defined forms."""
        forms = list_forms()
        assert "haiku" in forms
        assert "tanka" in forms
        assert "limerick" in forms
        assert "shakespearean" in forms
        assert "blank_verse" in forms
        assert "free_verse" in forms
        assert "villanelle" in forms
        assert "ghazal" in forms
        assert "pantoum" in forms
        assert "sestina" in forms
        assert len(forms) == 10


class TestGetRhymeGroups:
    """Tests for get_rhyme_groups function."""
    
    def test_abab_pattern(self):
        """ABAB groups alternating lines."""
        groups = get_rhyme_groups("ABAB")
        assert groups["A"] == [0, 2]
        assert groups["B"] == [1, 3]
    
    def test_aabba_pattern(self):
        """AABBA groups for limerick."""
        groups = get_rhyme_groups("AABBA")
        assert groups["A"] == [0, 1, 4]
        assert groups["B"] == [2, 3]
    
    def test_shakespearean_pattern(self):
        """Full Shakespearean sonnet rhyme scheme."""
        groups = get_rhyme_groups("ABABCDCDEFEFGG")
        assert groups["A"] == [0, 2]
        assert groups["B"] == [1, 3]
        assert groups["C"] == [4, 6]
        assert groups["D"] == [5, 7]
        assert groups["E"] == [8, 10]
        assert groups["F"] == [9, 11]
        assert groups["G"] == [12, 13]
    
    def test_lowercase_normalized(self):
        """Lowercase input normalized to uppercase."""
        groups = get_rhyme_groups("abab")
        assert "A" in groups
        assert "B" in groups


class TestGetSyllableTarget:
    """Tests for get_syllable_target function."""
    
    def test_list_syllables(self):
        """Get syllables from list for each line."""
        haiku = get_form("haiku")
        assert get_syllable_target(haiku, 0) == 5
        assert get_syllable_target(haiku, 1) == 7
        assert get_syllable_target(haiku, 2) == 5
    
    def test_uniform_syllables(self):
        """Get uniform syllables for any line."""
        sonnet = get_form("shakespearean")
        assert get_syllable_target(sonnet, 0) == 10
        assert get_syllable_target(sonnet, 5) == 10
        assert get_syllable_target(sonnet, 13) == 10
    
    def test_out_of_range_returns_zero(self):
        """Out of range line returns 0."""
        haiku = get_form("haiku")
        assert get_syllable_target(haiku, 10) == 0
    
    def test_free_verse_no_constraint(self):
        """Free verse returns 0 (no constraint)."""
        fv = get_form("free_verse")
        assert get_syllable_target(fv, 0) == 0


class TestSestinaForm:
    """Tests for sestina form and end-word rotation."""
    
    def test_sestina_structure(self):
        """Sestina has 39 lines (6 stanzas of 6 + 3-line envoi)."""
        sestina = FORMS["sestina"]
        assert sestina.name == "Sestina"
        assert sestina.lines == 39
        assert sestina.syllables == 10
        assert sestina.rhyme_scheme is None  # Uses end-word repetition instead
        assert sestina.meter == "iambic"
    
    def test_get_sestina_form(self):
        """Can get sestina via get_form."""
        form = get_form("sestina")
        assert form.name == "Sestina"
    
    def test_sestina_rotation_structure(self):
        """SESTINA_ROTATION has 6 stanzas with 6 positions each."""
        assert len(SESTINA_ROTATION) == 6
        for stanza in SESTINA_ROTATION:
            assert len(stanza) == 6
            # Each stanza uses all 6 words (1-6)
            assert sorted(stanza) == [1, 2, 3, 4, 5, 6]
    
    def test_sestina_rotation_first_stanza(self):
        """First stanza has words in original order."""
        assert SESTINA_ROTATION[0] == [1, 2, 3, 4, 5, 6]
    
    def test_sestina_rotation_pattern(self):
        """Rotation follows the spiral pattern (6,1,5,2,4,3)."""
        # Each stanza's order comes from previous via (6,1,5,2,4,3) mapping
        # Stanza 2 should be [6,1,5,2,4,3] of stanza 1
        assert SESTINA_ROTATION[1] == [6, 1, 5, 2, 4, 3]
    
    def test_sestina_envoi_structure(self):
        """Envoi uses pairs of words in middle/end positions."""
        assert len(SESTINA_ENVOI) == 3
        # Each line has two word positions
        for pair in SESTINA_ENVOI:
            assert len(pair) == 2
    
    def test_get_sestina_end_word_order_stanza_0(self):
        """Get end-word order for first stanza."""
        order = get_sestina_end_word_order(0)
        assert order == [1, 2, 3, 4, 5, 6]
    
    def test_get_sestina_end_word_order_stanza_5(self):
        """Get end-word order for last stanza."""
        order = get_sestina_end_word_order(5)
        assert order == [2, 4, 6, 5, 3, 1]
    
    def test_get_sestina_end_word_order_invalid(self):
        """Invalid stanza raises ValueError."""
        with pytest.raises(ValueError):
            get_sestina_end_word_order(6)
        with pytest.raises(ValueError):
            get_sestina_end_word_order(-1)
    
    def test_get_sestina_line_end_word(self):
        """Get correct end-word for each line."""
        # Line 0 (stanza 0, line 0) uses word 1
        assert get_sestina_line_end_word(0) == 1
        # Line 5 (stanza 0, line 5) uses word 6
        assert get_sestina_line_end_word(5) == 6
        # Line 6 (stanza 1, line 0) uses word 6
        assert get_sestina_line_end_word(6) == 6
        # Line 7 (stanza 1, line 1) uses word 1
        assert get_sestina_line_end_word(7) == 1
    
    def test_get_sestina_line_end_word_envoi(self):
        """Envoi lines return 0 (special handling needed)."""
        assert get_sestina_line_end_word(36) == 0
        assert get_sestina_line_end_word(37) == 0
        assert get_sestina_line_end_word(38) == 0
