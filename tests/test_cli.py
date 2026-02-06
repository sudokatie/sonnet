"""
Tests for cli.py - CLI commands.
"""

import pytest
import tempfile
import os
from typer.testing import CliRunner
from sonnet.cli import app

runner = CliRunner()


class TestMain:
    """Tests for main app."""
    
    def test_version_flag(self):
        """--version shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "sonnet" in result.output
    
    def test_no_args_shows_help(self):
        """No args shows help."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage" in result.output or "sonnet" in result.output


class TestFormsCommand:
    """Tests for forms command."""
    
    def test_list_forms(self):
        """Lists all available forms."""
        result = runner.invoke(app, ["forms"])
        assert result.exit_code == 0
        assert "haiku" in result.output.lower()
        assert "limerick" in result.output.lower()
    
    def test_show_form_details(self):
        """Show details for specific form."""
        result = runner.invoke(app, ["forms", "haiku"])
        assert result.exit_code == 0
        assert "Haiku" in result.output
        assert "5" in result.output  # syllables
    
    def test_unknown_form(self):
        """Unknown form shows error."""
        result = runner.invoke(app, ["forms", "nonexistent"])
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "unknown" in result.output.lower()


class TestCheckCommand:
    """Tests for check command."""
    
    def test_check_text(self):
        """Check poem from text."""
        result = runner.invoke(app, [
            "check",
            "--text", "An old silent pond / A frog jumps into water / Splash silence again",
            "--form", "haiku",
        ])
        # Just check it runs
        assert "Haiku" in result.output or "haiku" in result.output.lower()
    
    def test_check_file(self):
        """Check poem from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("An old silent pond\nA frog jumps in\nSplash\n")
            path = f.name
        
        try:
            result = runner.invoke(app, ["check", path, "--form", "haiku"])
            assert "Haiku" in result.output or "haiku" in result.output.lower()
        finally:
            os.unlink(path)
    
    def test_check_missing_input(self):
        """Check without input shows error."""
        result = runner.invoke(app, ["check", "--form", "haiku"])
        assert result.exit_code == 1
    
    def test_check_missing_file(self):
        """Check with missing file shows error."""
        result = runner.invoke(app, ["check", "/nonexistent/file.txt"])
        assert result.exit_code == 1


class TestGenerateCommand:
    """Tests for generate command."""
    
    def test_generate_requires_theme(self):
        """Generate requires --theme."""
        result = runner.invoke(app, ["generate"])
        assert result.exit_code != 0
    
    def test_generate_unknown_form(self):
        """Generate with unknown form fails."""
        result = runner.invoke(app, [
            "generate",
            "--form", "nonexistent",
            "--theme", "test",
        ])
        assert result.exit_code == 1


class TestInteractiveCommand:
    """Tests for interactive command."""
    
    def test_interactive_requires_theme(self):
        """Interactive requires --theme."""
        result = runner.invoke(app, ["interactive"])
        assert result.exit_code != 0
    
    def test_interactive_unknown_form(self):
        """Interactive with unknown form fails."""
        result = runner.invoke(app, [
            "interactive",
            "--form", "nonexistent",
            "--theme", "test",
        ])
        assert result.exit_code == 1
