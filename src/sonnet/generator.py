"""
LLM-based line generation for poetry.
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from sonnet.forms import FormDefinition, get_syllable_target, get_rhyme_groups


@dataclass
class GenerationConfig:
    """Configuration for LLM generation."""
    model: str = "llama3"
    api_url: str = "http://localhost:11434/api/generate"
    temperature: float = 0.8
    max_tokens: int = 200
    num_candidates: int = 5


@dataclass
class Candidate:
    """A generated line candidate."""
    text: str
    score: float = 0.0  # Constraint score (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)


def get_config_from_env() -> GenerationConfig:
    """Load generation config from environment variables."""
    return GenerationConfig(
        model=os.environ.get("SONNET_MODEL", "llama3"),
        api_url=os.environ.get("SONNET_API_URL", "http://localhost:11434/api/generate"),
        temperature=float(os.environ.get("SONNET_TEMPERATURE", "0.8")),
        max_tokens=int(os.environ.get("SONNET_MAX_TOKENS", "200")),
        num_candidates=int(os.environ.get("SONNET_CANDIDATES", "5")),
    )


def build_prompt(
    form: FormDefinition,
    theme: str,
    line_index: int,
    prior_lines: List[str],
    rhyme_word: Optional[str] = None,
) -> str:
    """
    Build a prompt for generating the next line.
    
    Args:
        form: The poetic form
        theme: Theme or topic of the poem
        line_index: Which line we're generating (0-indexed)
        prior_lines: Previously generated lines
        rhyme_word: Word that this line must rhyme with (if any)
    
    Returns:
        Prompt string for the LLM
    """
    target_syllables = get_syllable_target(form, line_index)
    
    prompt_parts = [
        f"You are writing a {form.name} about '{theme}'.",
        "",
    ]
    
    if prior_lines:
        prompt_parts.append("Lines so far:")
        for i, line in enumerate(prior_lines):
            prompt_parts.append(f"  {i + 1}. {line}")
        prompt_parts.append("")
    
    prompt_parts.append(f"Generate line {line_index + 1}.")
    
    constraints = []
    if target_syllables > 0:
        constraints.append(f"exactly {target_syllables} syllables")
    if rhyme_word:
        constraints.append(f"must rhyme with '{rhyme_word}'")
    if form.meter:
        constraints.append(f"{form.meter} meter")
    
    if constraints:
        prompt_parts.append(f"Constraints: {', '.join(constraints)}.")
    
    prompt_parts.extend([
        "",
        f"Provide {5} alternative lines, one per line, numbered 1-5.",
        "Just the lines, no explanations.",
    ])
    
    return "\n".join(prompt_parts)


def parse_candidates(response: str) -> List[str]:
    """
    Parse numbered lines from LLM response.
    
    Args:
        response: Raw LLM response text
    
    Returns:
        List of extracted line candidates
    """
    candidates = []
    
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        
        # Remove numbering like "1.", "1)", "1:"
        match = re.match(r"^\d+[\.\)\:]?\s*(.+)$", line)
        if match:
            candidates.append(match.group(1).strip())
        elif not line[0].isdigit():
            # Unnumbered lines
            candidates.append(line)
    
    return candidates


def call_llm(prompt: str, config: GenerationConfig) -> str:
    """
    Call the LLM API to generate text.
    
    Args:
        prompt: The prompt to send
        config: Generation configuration
    
    Returns:
        Generated text response
    
    Raises:
        RuntimeError: If httpx not available or API call fails
    """
    if not HAS_HTTPX:
        raise RuntimeError("httpx is required for LLM calls: pip install httpx")
    
    payload = {
        "model": config.model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": config.temperature,
            "num_predict": config.max_tokens,
        }
    }
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(config.api_url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}")


def generate_candidates(
    form: FormDefinition,
    theme: str,
    line_index: int,
    prior_lines: List[str],
    rhyme_word: Optional[str] = None,
    config: Optional[GenerationConfig] = None,
) -> List[Candidate]:
    """
    Generate candidate lines for the next line of a poem.
    
    Args:
        form: The poetic form
        theme: Theme or topic
        line_index: Which line we're generating
        prior_lines: Previously generated lines
        rhyme_word: Word that this line must rhyme with
        config: Generation configuration (uses env if None)
    
    Returns:
        List of Candidate objects
    """
    if config is None:
        config = get_config_from_env()
    
    prompt = build_prompt(form, theme, line_index, prior_lines, rhyme_word)
    response = call_llm(prompt, config)
    lines = parse_candidates(response)
    
    return [Candidate(text=line) for line in lines[:config.num_candidates]]


def get_ending_word(line: str) -> Optional[str]:
    """
    Extract the last word from a line, ignoring punctuation.
    
    Args:
        line: A line of poetry
    
    Returns:
        The last word, or None if line is empty
    """
    # Remove trailing punctuation and get words
    cleaned = re.sub(r'[^\w\s]', '', line.strip())
    words = cleaned.split()
    return words[-1].lower() if words else None


def get_rhyme_word_for_line(
    form: FormDefinition,
    line_index: int,
    prior_lines: List[str],
) -> Optional[str]:
    """
    Determine what word the current line should rhyme with.
    
    Looks at the rhyme scheme to find prior lines that share
    the same rhyme letter, then extracts their ending word.
    
    Args:
        form: The poetic form (with rhyme_scheme)
        line_index: Current line index (0-based)
        prior_lines: Previously generated lines
    
    Returns:
        Word to rhyme with, or None if no constraint
    """
    if not form.rhyme_scheme:
        return None
    
    scheme = form.rhyme_scheme.upper()
    if line_index >= len(scheme):
        return None
    
    current_letter = scheme[line_index]
    
    # Find the first prior line with the same letter
    for prior_idx in range(line_index):
        if prior_idx < len(scheme) and scheme[prior_idx] == current_letter:
            # This prior line should rhyme with us
            if prior_idx < len(prior_lines):
                return get_ending_word(prior_lines[prior_idx])
    
    return None


def generate_poem(
    form: FormDefinition,
    theme: str,
    config: Optional[GenerationConfig] = None,
) -> List[str]:
    """
    Generate a complete poem.
    
    Args:
        form: The poetic form
        theme: Theme or topic
        config: Generation configuration
    
    Returns:
        List of lines making up the poem
    """
    if config is None:
        config = get_config_from_env()
    
    lines = []
    
    for i in range(form.lines):
        # Determine rhyme word from prior lines and rhyme scheme
        rhyme_word = get_rhyme_word_for_line(form, i, lines)
        
        candidates = generate_candidates(
            form=form,
            theme=theme,
            line_index=i,
            prior_lines=lines,
            rhyme_word=rhyme_word,
            config=config,
        )
        
        if candidates:
            # Just take the first for now
            # TODO: Use ranker to pick best
            lines.append(candidates[0].text)
        else:
            lines.append("")
    
    return lines
