"""
Configuration loading for Sonnet.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import tomli
    HAS_TOMLI = True
except ImportError:
    HAS_TOMLI = False


@dataclass
class SonnetConfig:
    """Full configuration for Sonnet."""
    # LLM settings
    model: str = "llama3"
    api_url: str = "http://localhost:11434/api/generate"
    temperature: float = 0.8
    max_tokens: int = 200
    num_candidates: int = 5
    
    # Output settings
    output_dir: str = "."
    auto_save: bool = True
    
    # UI settings
    color: bool = True
    verbose: bool = False


DEFAULT_CONFIG_PATHS = [
    Path.home() / ".config" / "sonnet" / "config.toml",
    Path.home() / ".sonnetrc",
    Path("sonnet.toml"),
]


def load_config_file(path: Path) -> Dict[str, Any]:
    """
    Load config from a TOML file.
    
    Args:
        path: Path to config file
    
    Returns:
        Dict of config values
    
    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If tomli not available
    """
    if not HAS_TOMLI:
        raise RuntimeError("tomli required to load config files: pip install tomli")
    
    with open(path, "rb") as f:
        return tomli.load(f)


def load_config(
    config_path: Optional[Path] = None,
) -> SonnetConfig:
    """
    Load configuration from environment variables and/or config file.
    
    Priority (highest to lowest):
    1. Environment variables (SONNET_*)
    2. Explicit config file
    3. Default config file locations
    4. Built-in defaults
    
    Args:
        config_path: Explicit path to config file
    
    Returns:
        SonnetConfig with merged values
    """
    config = SonnetConfig()
    
    # Try to load from file
    file_config: Dict[str, Any] = {}
    
    paths_to_try = [config_path] if config_path else DEFAULT_CONFIG_PATHS
    for path in paths_to_try:
        if path and path.exists():
            try:
                file_config = load_config_file(path)
                break
            except Exception:
                pass  # Silently continue to next path
    
    # Apply file config
    if "model" in file_config:
        config.model = str(file_config["model"])
    if "api_url" in file_config:
        config.api_url = str(file_config["api_url"])
    if "temperature" in file_config:
        config.temperature = float(file_config["temperature"])
    if "max_tokens" in file_config:
        config.max_tokens = int(file_config["max_tokens"])
    if "num_candidates" in file_config:
        config.num_candidates = int(file_config["num_candidates"])
    if "output_dir" in file_config:
        config.output_dir = str(file_config["output_dir"])
    if "auto_save" in file_config:
        config.auto_save = bool(file_config["auto_save"])
    if "color" in file_config:
        config.color = bool(file_config["color"])
    if "verbose" in file_config:
        config.verbose = bool(file_config["verbose"])
    
    # Environment variables override everything
    env_model = os.environ.get("SONNET_MODEL")
    if env_model:
        config.model = env_model
    
    env_url = os.environ.get("SONNET_API_URL")
    if env_url:
        config.api_url = env_url
    
    env_temp = os.environ.get("SONNET_TEMPERATURE")
    if env_temp:
        config.temperature = float(env_temp)
    
    env_tokens = os.environ.get("SONNET_MAX_TOKENS")
    if env_tokens:
        config.max_tokens = int(env_tokens)
    
    env_cands = os.environ.get("SONNET_CANDIDATES")
    if env_cands:
        config.num_candidates = int(env_cands)
    
    env_out = os.environ.get("SONNET_OUTPUT_DIR")
    if env_out:
        config.output_dir = env_out
    
    env_save = os.environ.get("SONNET_AUTO_SAVE")
    if env_save:
        config.auto_save = env_save.lower() in ("true", "1", "yes")
    
    env_color = os.environ.get("SONNET_COLOR")
    if env_color:
        config.color = env_color.lower() in ("true", "1", "yes")
    
    env_verbose = os.environ.get("SONNET_VERBOSE")
    if env_verbose:
        config.verbose = env_verbose.lower() in ("true", "1", "yes")
    
    return config


def get_model() -> str:
    """Get the configured model name."""
    return load_config().model


def get_api_url() -> str:
    """Get the configured API URL."""
    return load_config().api_url
