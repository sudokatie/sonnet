"""
Tests for generator.py - LLM-based line generation.
"""

import pytest
from unittest.mock import patch, MagicMock
from sonnet.generator import (
    GenerationConfig,
    Candidate,
    build_prompt,
    parse_candidates,
    get_config_from_env,
    call_llm,
    generate_candidates,
)
from sonnet.forms import get_form


class TestGenerationConfig:
    """Tests for GenerationConfig."""
    
    def test_defaults(self):
        """Default config values."""
        config = GenerationConfig()
        assert config.model == "llama3"
        assert config.temperature == 0.8
        assert config.num_candidates == 5
    
    def test_custom_values(self):
        """Custom config values."""
        config = GenerationConfig(
            model="gemma2",
            temperature=0.5,
            num_candidates=3,
        )
        assert config.model == "gemma2"
        assert config.temperature == 0.5


class TestGetConfigFromEnv:
    """Tests for env config loading."""
    
    def test_default_when_no_env(self):
        """Uses defaults when env vars not set."""
        with patch.dict("os.environ", {}, clear=True):
            config = get_config_from_env()
            assert config.model == "llama3"
    
    def test_reads_env_vars(self):
        """Reads from environment variables."""
        with patch.dict("os.environ", {"SONNET_MODEL": "qwen2"}):
            config = get_config_from_env()
            assert config.model == "qwen2"


class TestBuildPrompt:
    """Tests for prompt building."""
    
    def test_basic_prompt(self):
        """Basic prompt structure."""
        form = get_form("haiku")
        prompt = build_prompt(form, "autumn", 0, [])
        assert "Haiku" in prompt
        assert "autumn" in prompt
        assert "line 1" in prompt.lower()
    
    def test_includes_prior_lines(self):
        """Prompt includes prior lines."""
        form = get_form("haiku")
        prior = ["First line here"]
        prompt = build_prompt(form, "autumn", 1, prior)
        assert "First line here" in prompt
        assert "line 2" in prompt.lower()
    
    def test_includes_syllable_constraint(self):
        """Prompt mentions syllable count."""
        form = get_form("haiku")
        prompt = build_prompt(form, "autumn", 0, [])
        assert "5 syllables" in prompt
    
    def test_includes_rhyme_constraint(self):
        """Prompt mentions rhyme word."""
        form = get_form("limerick")
        prompt = build_prompt(form, "cat", 1, ["line one"], rhyme_word="Maine")
        assert "rhyme" in prompt.lower()
        assert "Maine" in prompt
    
    def test_includes_meter_constraint(self):
        """Prompt mentions meter."""
        form = get_form("shakespearean")
        prompt = build_prompt(form, "love", 0, [])
        assert "iambic" in prompt.lower()


class TestParseCandidates:
    """Tests for parsing LLM output."""
    
    def test_numbered_lines(self):
        """Parse numbered lines."""
        response = """1. First candidate line
2. Second candidate line
3. Third candidate line"""
        candidates = parse_candidates(response)
        assert len(candidates) == 3
        assert candidates[0] == "First candidate line"
    
    def test_period_numbering(self):
        """Parse period numbering: 1. 2. 3."""
        response = "1. Line one\n2. Line two"
        candidates = parse_candidates(response)
        assert len(candidates) == 2
    
    def test_parenthesis_numbering(self):
        """Parse paren numbering: 1) 2) 3)."""
        response = "1) Line one\n2) Line two"
        candidates = parse_candidates(response)
        assert len(candidates) == 2
    
    def test_colon_numbering(self):
        """Parse colon numbering: 1: 2: 3:."""
        response = "1: Line one\n2: Line two"
        candidates = parse_candidates(response)
        assert len(candidates) == 2
    
    def test_empty_lines_skipped(self):
        """Empty lines are skipped."""
        response = "1. Line one\n\n2. Line two"
        candidates = parse_candidates(response)
        assert len(candidates) == 2
    
    def test_unnumbered_lines(self):
        """Parse unnumbered lines."""
        response = "Line one\nLine two\nLine three"
        candidates = parse_candidates(response)
        assert len(candidates) == 3


class TestCallLLM:
    """Tests for LLM API calls."""
    
    def test_requires_httpx(self):
        """Raises error if httpx not available."""
        with patch("sonnet.generator.HAS_HTTPX", False):
            config = GenerationConfig()
            with pytest.raises(RuntimeError, match="httpx"):
                call_llm("test prompt", config)
    
    @patch("sonnet.generator.HAS_HTTPX", True)
    @patch("sonnet.generator.httpx")
    def test_calls_api(self, mock_httpx):
        """Calls the API with correct payload."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Generated text"}
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client
        
        config = GenerationConfig(model="test-model")
        result = call_llm("test prompt", config)
        
        assert result == "Generated text"
        mock_client.post.assert_called_once()


class TestGenerateCandidates:
    """Tests for candidate generation."""
    
    @patch("sonnet.generator.call_llm")
    def test_returns_candidates(self, mock_llm):
        """Returns list of Candidate objects."""
        mock_llm.return_value = "1. Line one\n2. Line two\n3. Line three"
        
        form = get_form("haiku")
        config = GenerationConfig(num_candidates=3)
        candidates = generate_candidates(
            form=form,
            theme="autumn",
            line_index=0,
            prior_lines=[],
            config=config,
        )
        
        assert len(candidates) == 3
        assert all(isinstance(c, Candidate) for c in candidates)
        assert candidates[0].text == "Line one"
    
    @patch("sonnet.generator.call_llm")
    def test_respects_num_candidates(self, mock_llm):
        """Limits to num_candidates."""
        mock_llm.return_value = "1. A\n2. B\n3. C\n4. D\n5. E\n6. F"
        
        form = get_form("haiku")
        config = GenerationConfig(num_candidates=3)
        candidates = generate_candidates(
            form=form,
            theme="test",
            line_index=0,
            prior_lines=[],
            config=config,
        )
        
        assert len(candidates) == 3
