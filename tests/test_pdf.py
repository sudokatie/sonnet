"""Tests for PDF export functionality."""

import pytest
from pathlib import Path
import tempfile

from sonnet.pdf import PdfExporter, PdfStyle, Poem, poems_to_pdf


class TestPoem:
    """Tests for Poem class."""

    def test_from_text_single_stanza(self):
        text = "Line one\nLine two\nLine three"
        poem = Poem.from_text(text, title="Test")
        
        assert poem.title == "Test"
        assert len(poem.stanzas) == 1
        assert poem.stanzas[0] == ["Line one", "Line two", "Line three"]

    def test_from_text_multiple_stanzas(self):
        text = "First line\nSecond line\n\nThird line\nFourth line"
        poem = Poem.from_text(text, title="Multi")
        
        assert len(poem.stanzas) == 2
        assert poem.stanzas[0] == ["First line", "Second line"]
        assert poem.stanzas[1] == ["Third line", "Fourth line"]

    def test_from_text_with_author(self):
        text = "A single line"
        poem = Poem.from_text(text, title="Solo", author="Test Author")
        
        assert poem.author == "Test Author"

    def test_from_text_strips_whitespace(self):
        text = "\n\nLine one\n\n\nLine two\n\n"
        poem = Poem.from_text(text)
        
        assert len(poem.stanzas) == 2


class TestPdfStyle:
    """Tests for PdfStyle configuration."""

    def test_default_values(self):
        style = PdfStyle()
        
        assert style.page_size == "letter"
        assert style.margin_top == 1.0
        assert style.title_font == "Times-Bold"
        assert style.body_font == "Times-Roman"

    def test_get_page_size_letter(self):
        style = PdfStyle(page_size="letter")
        from reportlab.lib.pagesizes import LETTER
        
        assert style.get_page_size() == LETTER

    def test_get_page_size_a4(self):
        style = PdfStyle(page_size="a4")
        from reportlab.lib.pagesizes import A4
        
        assert style.get_page_size() == A4

    def test_custom_margins(self):
        style = PdfStyle(
            margin_top=1.5,
            margin_bottom=1.5,
            margin_left=2.0,
            margin_right=2.0,
        )
        
        assert style.margin_top == 1.5
        assert style.margin_left == 2.0


class TestPdfExporter:
    """Tests for PDF export functionality."""

    def test_export_single_poem(self):
        poem = Poem(
            title="Test Poem",
            stanzas=[["Line one", "Line two", "Line three"]],
        )
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output = Path(f.name)
        
        try:
            exporter = PdfExporter()
            result = exporter.export_single(poem, output)
            
            assert result.exists()
            assert result.stat().st_size > 0
            
            # Check it's a valid PDF (starts with %PDF)
            with open(result, "rb") as f:
                header = f.read(4)
                assert header == b"%PDF"
        finally:
            output.unlink(missing_ok=True)

    def test_export_multiple_poems(self):
        poems = [
            Poem(title="First", stanzas=[["Hello", "World"]]),
            Poem(title="Second", stanzas=[["Goodbye", "World"]]),
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output = Path(f.name)
        
        try:
            exporter = PdfExporter()
            result = exporter.export(poems, output)
            
            assert result.exists()
            assert result.stat().st_size > 0
        finally:
            output.unlink(missing_ok=True)

    def test_export_with_custom_style(self):
        poem = Poem(title="Styled", stanzas=[["A styled poem"]])
        style = PdfStyle(
            title_font="Helvetica-Bold",
            body_font="Helvetica",
            center_poems=True,
        )
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output = Path(f.name)
        
        try:
            exporter = PdfExporter(style)
            result = exporter.export_single(poem, output)
            
            assert result.exists()
        finally:
            output.unlink(missing_ok=True)

    def test_export_with_author(self):
        poem = Poem(
            title="Authored",
            stanzas=[["A poem with author"]],
            author="Test Author",
        )
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output = Path(f.name)
        
        try:
            exporter = PdfExporter()
            result = exporter.export_single(poem, output)
            
            assert result.exists()
        finally:
            output.unlink(missing_ok=True)


class TestConvenienceFunction:
    """Tests for poems_to_pdf helper."""

    def test_poems_to_pdf(self):
        poems = [Poem(title="Quick", stanzas=[["Fast export"]])]
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output = Path(f.name)
        
        try:
            result = poems_to_pdf(poems, output)
            
            assert result.exists()
            assert result == output
        finally:
            output.unlink(missing_ok=True)

    def test_poems_to_pdf_with_style(self):
        poems = [Poem(title="Styled Quick", stanzas=[["Styled fast"]])]
        style = PdfStyle(page_size="a4")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output = Path(f.name)
        
        try:
            result = poems_to_pdf(poems, output, style=style)
            
            assert result.exists()
        finally:
            output.unlink(missing_ok=True)
