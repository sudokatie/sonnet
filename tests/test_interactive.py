"""
Tests for interactive.py - TUI helpers.
"""

import pytest
import json
import tempfile
import os
from sonnet.interactive import (
    PoemProgress,
    save_progress,
    load_progress,
)


class TestPoemProgress:
    """Tests for PoemProgress dataclass."""
    
    def test_create_progress(self):
        """Create a progress object."""
        progress = PoemProgress(
            form_name="haiku",
            theme="autumn",
            lines=["first line"],
            current_line=1,
        )
        assert progress.form_name == "haiku"
        assert progress.theme == "autumn"
        assert len(progress.lines) == 1
    
    def test_default_current_line(self):
        """Default current_line is 0."""
        progress = PoemProgress(
            form_name="haiku",
            theme="test",
            lines=[],
        )
        assert progress.current_line == 0


class TestSaveProgress:
    """Tests for save_progress function."""
    
    def test_save_creates_file(self):
        """Save creates a JSON file."""
        progress = PoemProgress(
            form_name="haiku",
            theme="test",
            lines=["line one", "line two"],
            current_line=2,
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        
        try:
            save_progress(progress, path)
            assert os.path.exists(path)
            
            with open(path, "r") as f:
                data = json.load(f)
            
            assert data["form_name"] == "haiku"
            assert data["theme"] == "test"
            assert data["lines"] == ["line one", "line two"]
        finally:
            os.unlink(path)
    
    def test_save_overwrites(self):
        """Save overwrites existing file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
            f.write('{"old": "data"}')
        
        try:
            progress = PoemProgress("test", "theme", ["new"])
            save_progress(progress, path)
            
            with open(path, "r") as f:
                data = json.load(f)
            
            assert "old" not in data
            assert data["form_name"] == "test"
        finally:
            os.unlink(path)


class TestLoadProgress:
    """Tests for load_progress function."""
    
    def test_load_valid_file(self):
        """Load a valid progress file."""
        data = {
            "form_name": "limerick",
            "theme": "humor",
            "lines": ["line 1", "line 2"],
            "current_line": 2,
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        
        try:
            progress = load_progress(path)
            assert progress.form_name == "limerick"
            assert progress.theme == "humor"
            assert progress.lines == ["line 1", "line 2"]
            assert progress.current_line == 2
        finally:
            os.unlink(path)
    
    def test_load_missing_current_line(self):
        """Load file without current_line uses len(lines)."""
        data = {
            "form_name": "haiku",
            "theme": "nature",
            "lines": ["one", "two", "three"],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        
        try:
            progress = load_progress(path)
            assert progress.current_line == 3  # len(lines)
        finally:
            os.unlink(path)
    
    def test_load_missing_file(self):
        """Load raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_progress("/nonexistent/path.json")
    
    def test_load_invalid_format(self):
        """Load raises ValueError for invalid format."""
        data = {"wrong": "format"}
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid progress file"):
                load_progress(path)
        finally:
            os.unlink(path)


class TestRoundTrip:
    """Tests for save/load round trip."""
    
    def test_save_load_roundtrip(self):
        """Data survives save and load."""
        original = PoemProgress(
            form_name="shakespearean",
            theme="love and loss",
            lines=["Line 1", "Line 2", "Line 3"],
            current_line=3,
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        
        try:
            save_progress(original, path)
            loaded = load_progress(path)
            
            assert loaded.form_name == original.form_name
            assert loaded.theme == original.theme
            assert loaded.lines == original.lines
            assert loaded.current_line == original.current_line
        finally:
            os.unlink(path)
