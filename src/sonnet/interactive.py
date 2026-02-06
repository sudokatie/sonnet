"""
Interactive TUI for line-by-line poetry composition.
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, IntPrompt
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from sonnet.forms import FormDefinition, get_form, get_syllable_target
from sonnet.ranker import RankedCandidate, Constraints, rank_candidates
from sonnet.generator import generate_candidates, GenerationConfig


@dataclass
class PoemProgress:
    """State of poem being composed."""
    form_name: str
    theme: str
    lines: List[str]
    current_line: int = 0


def save_progress(progress: PoemProgress, path: str) -> None:
    """
    Save poem progress to a JSON file.
    
    Args:
        progress: Current poem state
        path: File path to save to
    """
    with open(path, "w") as f:
        json.dump(asdict(progress), f, indent=2)


def load_progress(path: str) -> PoemProgress:
    """
    Load poem progress from a JSON file.
    
    Args:
        path: File path to load from
    
    Returns:
        PoemProgress object
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    with open(path, "r") as f:
        data = json.load(f)
    
    required = {"form_name", "theme", "lines"}
    if not required.issubset(data.keys()):
        raise ValueError(f"Invalid progress file: missing {required - set(data.keys())}")
    
    return PoemProgress(
        form_name=data["form_name"],
        theme=data["theme"],
        lines=data["lines"],
        current_line=data.get("current_line", len(data["lines"])),
    )


def display_progress(
    console: "Console",
    form: FormDefinition,
    lines: List[str],
    current_line: int,
) -> None:
    """
    Display current poem progress.
    
    Args:
        console: Rich console
        form: Poetic form
        lines: Lines composed so far
        current_line: Which line we're working on
    """
    table = Table(title=f"{form.name} - Progress", show_header=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Line", style="white")
    table.add_column("Syllables", justify="right", width=10)
    
    for i in range(form.lines):
        line_num = str(i + 1)
        if i < len(lines):
            text = lines[i]
            target = get_syllable_target(form, i)
            syl_str = str(target) if target > 0 else "-"
        elif i == current_line:
            text = "[yellow]<writing...>[/yellow]"
            target = get_syllable_target(form, i)
            syl_str = str(target) if target > 0 else "-"
        else:
            text = "[dim]...[/dim]"
            target = get_syllable_target(form, i)
            syl_str = str(target) if target > 0 else "-"
        
        table.add_row(line_num, text, syl_str)
    
    console.print(table)


def display_candidates(
    console: "Console",
    candidates: List[RankedCandidate],
) -> None:
    """
    Display ranked candidates for selection.
    
    Args:
        console: Rich console
        candidates: Ranked candidate lines
    """
    table = Table(title="Candidates", show_header=True)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Line", style="white")
    table.add_column("Score", justify="right", width=8)
    
    for i, c in enumerate(candidates[:5]):
        score_str = f"{c.score.total:.0%}"
        table.add_row(str(i + 1), c.text, score_str)
    
    console.print(table)
    console.print("\n[dim]Enter 1-5 to select, 'r' to regenerate, 'e' to edit, 'q' to quit[/dim]")


def get_user_selection(console: "Console", count: int) -> str:
    """
    Get user's selection from candidates.
    
    Args:
        console: Rich console
        count: Number of candidates
    
    Returns:
        User input string (number, 'r', 'e', or 'q')
    """
    while True:
        choice = Prompt.ask("Select")
        choice = choice.strip().lower()
        
        if choice in ("r", "e", "q"):
            return choice
        
        try:
            num = int(choice)
            if 1 <= num <= count:
                return choice
            console.print(f"[red]Please enter 1-{count}[/red]")
        except ValueError:
            console.print("[red]Invalid input[/red]")


def run_interactive(
    form: FormDefinition,
    theme: str,
    config: Optional[GenerationConfig] = None,
    save_path: Optional[str] = None,
) -> List[str]:
    """
    Run the interactive TUI for poem composition.
    
    Args:
        form: Poetic form to write
        theme: Theme or topic
        config: Generation config (uses default if None)
        save_path: Path to auto-save progress
    
    Returns:
        List of completed poem lines
    """
    if not HAS_RICH:
        raise RuntimeError("Rich is required for interactive mode: pip install rich")
    
    console = Console()
    lines: List[str] = []
    
    console.print(Panel(
        f"[bold]Writing a {form.name}[/bold]\nTheme: {theme}\nLines: {form.lines}",
        title="Sonnet",
    ))
    
    for line_idx in range(form.lines):
        console.print(f"\n[bold cyan]Line {line_idx + 1} of {form.lines}[/bold cyan]")
        display_progress(console, form, lines, line_idx)
        
        # Build constraints for this line
        target_syllables = get_syllable_target(form, line_idx)
        constraints = Constraints(
            target_syllables=target_syllables,
            meter=form.meter,
        )
        
        while True:
            # Generate candidates
            console.print("\n[dim]Generating candidates...[/dim]")
            try:
                raw_candidates = generate_candidates(
                    form=form,
                    theme=theme,
                    line_index=line_idx,
                    prior_lines=lines,
                    config=config,
                )
                candidate_texts = [c.text for c in raw_candidates]
            except Exception as e:
                console.print(f"[red]Generation failed: {e}[/red]")
                candidate_texts = []
            
            if not candidate_texts:
                # Fallback: let user type
                console.print("[yellow]No candidates generated. Please type manually.[/yellow]")
                user_line = Prompt.ask("Your line")
                lines.append(user_line)
                break
            
            # Rank candidates
            ranked = rank_candidates(candidate_texts, constraints)
            display_candidates(console, ranked)
            
            choice = get_user_selection(console, len(ranked))
            
            if choice == "q":
                console.print("[yellow]Saving and exiting...[/yellow]")
                if save_path:
                    progress = PoemProgress(form.name, theme, lines, line_idx)
                    save_progress(progress, save_path)
                return lines
            elif choice == "r":
                continue  # Regenerate
            elif choice == "e":
                user_line = Prompt.ask("Your line")
                lines.append(user_line)
                break
            else:
                idx = int(choice) - 1
                lines.append(ranked[idx].text)
                break
        
        # Auto-save after each line
        if save_path:
            progress = PoemProgress(form.name, theme, lines, line_idx + 1)
            save_progress(progress, save_path)
    
    # Complete!
    console.print("\n[bold green]Poem complete![/bold green]\n")
    display_progress(console, form, lines, form.lines)
    
    return lines
