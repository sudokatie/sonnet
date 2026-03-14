"""PDF export for poems with configurable typography."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from reportlab.lib.pagesizes import LETTER, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


@dataclass
class PdfStyle:
    """Typography and layout settings for PDF export."""

    # Page size
    page_size: str = "letter"  # "letter" or "a4"

    # Margins (in inches)
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.25
    margin_right: float = 1.25

    # Title styling
    title_font: str = "Times-Bold"
    title_size: int = 18
    title_spacing: float = 0.3  # inches after title

    # Body styling
    body_font: str = "Times-Roman"
    body_size: int = 12
    line_spacing: float = 1.4  # multiplier

    # Poem spacing
    poem_spacing: float = 0.5  # inches between poems
    stanza_spacing: float = 0.25  # inches between stanzas

    # Layout
    center_poems: bool = False
    page_break_between: bool = False

    def get_page_size(self):
        """Get reportlab page size tuple."""
        return A4 if self.page_size.lower() == "a4" else LETTER


@dataclass
class Poem:
    """A poem with title and stanzas."""

    title: str
    stanzas: List[List[str]] = field(default_factory=list)
    author: Optional[str] = None

    @classmethod
    def from_text(cls, text: str, title: str = "", author: Optional[str] = None) -> "Poem":
        """Parse poem text into stanzas (separated by blank lines)."""
        lines = text.strip().split("\n")
        stanzas: List[List[str]] = []
        current: List[str] = []

        for line in lines:
            if line.strip() == "":
                if current:
                    stanzas.append(current)
                    current = []
            else:
                current.append(line)

        if current:
            stanzas.append(current)

        return cls(title=title, stanzas=stanzas, author=author)


class PdfExporter:
    """Export poems to PDF with configurable styling."""

    def __init__(self, style: Optional[PdfStyle] = None):
        self.style = style or PdfStyle()
        self._title_style: Optional[ParagraphStyle] = None
        self._body_style: Optional[ParagraphStyle] = None
        self._author_style: Optional[ParagraphStyle] = None

    def _build_styles(self) -> None:
        """Build paragraph styles from configuration."""
        alignment = TA_CENTER if self.style.center_poems else TA_LEFT

        self._title_style = ParagraphStyle(
            "PoemTitle",
            fontName=self.style.title_font,
            fontSize=self.style.title_size,
            alignment=alignment,
            spaceAfter=self.style.title_spacing * inch,
        )

        self._body_style = ParagraphStyle(
            "PoemBody",
            fontName=self.style.body_font,
            fontSize=self.style.body_size,
            alignment=alignment,
            leading=self.style.body_size * self.style.line_spacing,
        )

        self._author_style = ParagraphStyle(
            "PoemAuthor",
            fontName=f"{self.style.body_font}",
            fontSize=self.style.body_size - 1,
            alignment=alignment,
            fontStyle="italic",
            spaceBefore=self.style.stanza_spacing * inch,
        )

    def _poem_to_flowables(self, poem: Poem, is_last: bool = False) -> list:
        """Convert a poem to reportlab flowables."""
        assert self._title_style is not None
        assert self._body_style is not None
        assert self._author_style is not None

        elements = []

        # Title
        if poem.title:
            elements.append(Paragraph(poem.title, self._title_style))

        # Stanzas
        for i, stanza in enumerate(poem.stanzas):
            # Join lines with <br/> for reportlab
            stanza_text = "<br/>".join(line for line in stanza)
            elements.append(Paragraph(stanza_text, self._body_style))

            # Stanza spacing (except after last stanza)
            if i < len(poem.stanzas) - 1:
                elements.append(Spacer(1, self.style.stanza_spacing * inch))

        # Author
        if poem.author:
            elements.append(Paragraph(f"— {poem.author}", self._author_style))

        # Spacing between poems
        if not is_last:
            if self.style.page_break_between:
                elements.append(PageBreak())
            else:
                elements.append(Spacer(1, self.style.poem_spacing * inch))

        return elements

    def export(self, poems: List[Poem], output_path: Path) -> Path:
        """Export poems to a PDF file."""
        self._build_styles()

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.style.get_page_size(),
            topMargin=self.style.margin_top * inch,
            bottomMargin=self.style.margin_bottom * inch,
            leftMargin=self.style.margin_left * inch,
            rightMargin=self.style.margin_right * inch,
        )

        elements = []
        for i, poem in enumerate(poems):
            is_last = i == len(poems) - 1
            elements.extend(self._poem_to_flowables(poem, is_last))

        doc.build(elements)
        return output_path

    def export_single(self, poem: Poem, output_path: Path) -> Path:
        """Export a single poem to PDF."""
        return self.export([poem], output_path)


def poems_to_pdf(
    poems: List[Poem],
    output: Path,
    style: Optional[PdfStyle] = None,
) -> Path:
    """Convenience function to export poems to PDF."""
    exporter = PdfExporter(style)
    return exporter.export(poems, output)
