"""
Tests for config.py - configuration loading.
"""

import pytest
import os
from unittest.mock import patch
from sonnet.config import (
    SonnetConfig,
    load_config,
    get_model,
    get_api_url,
)


class TestSonnetConfig:
    """Tests for SonnetConfig dataclass."""
    
    def test_defaults(self):
        """Default config values."""
        config = SonnetConfig()
        assert config.model == "llama3"
        assert config.temperature == 0.8
        assert config.num_candidates == 5
        assert config.color is True
    
    def test_custom_values(self):
        """Custom config values."""
        config = SonnetConfig(
            model="gemma2",
            temperature=0.5,
            verbose=True,
        )
        assert config.model == "gemma2"
        assert config.temperature == 0.5
        assert config.verbose is True


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_returns_config(self):
        """Returns a SonnetConfig object."""
        config = load_config()
        assert isinstance(config, SonnetConfig)
    
    def test_env_override_model(self):
        """Environment variables override defaults."""
        with patch.dict(os.environ, {"SONNET_MODEL": "custom-model"}):
            config = load_config()
            assert config.model == "custom-model"
    
    def test_env_override_temperature(self):
        """SONNET_TEMPERATURE env var."""
        with patch.dict(os.environ, {"SONNET_TEMPERATURE": "0.3"}):
            config = load_config()
            assert config.temperature == 0.3
    
    def test_env_override_bool_true(self):
        """Boolean env vars work with various true values."""
        with patch.dict(os.environ, {"SONNET_VERBOSE": "true"}):
            config = load_config()
            assert config.verbose is True
        
        with patch.dict(os.environ, {"SONNET_VERBOSE": "1"}):
            config = load_config()
            assert config.verbose is True
    
    def test_env_override_bool_false(self):
        """Boolean env vars default to False for other values."""
        with patch.dict(os.environ, {"SONNET_VERBOSE": "false"}):
            config = load_config()
            assert config.verbose is False


class TestGetModel:
    """Tests for get_model helper."""
    
    def test_returns_model(self):
        """Returns model name."""
        with patch.dict(os.environ, {}, clear=True):
            model = get_model()
            assert isinstance(model, str)
            assert len(model) > 0


class TestGetApiUrl:
    """Tests for get_api_url helper."""
    
    def test_returns_url(self):
        """Returns API URL."""
        url = get_api_url()
        assert isinstance(url, str)
        assert url.startswith("http")
