"""CLI entry point for Sonnet."""

from __future__ import annotations
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table

from sonnet import __version__
from sonnet.forms import get_form, list_forms, FormDefinition
from sonnet.checker import check_poem, format_analysis
from sonnet.generator import generate_poem, GenerationConfig

app = typer.Typer(
    name="sonnet",
    help="Constraint-based poetry generator. Rules breed creativity.",
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """Sonnet: Generate poetry that respects form."""
    if version:
        typer.echo(f"sonnet {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def generate(
    form: str = typer.Option("haiku", "--form", "-f", help="Poetic form"),
    theme: str = typer.Option(..., "--theme", "-t", help="Theme or topic"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    model: str = typer.Option("llama3", "--model", "-m", help="LLM model name"),
):
    """Generate a complete poem."""
    try:
        form_def = get_form(form)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold]Generating {form_def.name}...[/bold]")
    console.print(f"Theme: {theme}\n")
    
    config = GenerationConfig(model=model)
    
    try:
        lines = generate_poem(form_def, theme, config)
    except Exception as e:
        console.print(f"[red]Generation failed: {e}[/red]")
        raise typer.Exit(1)
    
    poem_text = "\n".join(lines)
    
    if output:
        output.write_text(poem_text)
        console.print(f"[green]Saved to {output}[/green]")
    else:
        console.print("[bold green]Generated poem:[/bold green]\n")
        console.print(poem_text)


@app.command()
def check(
    file: Optional[Path] = typer.Argument(None, help="File containing poem"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Poem text (use / for line breaks)"),
    form: str = typer.Option("haiku", "--form", "-f", help="Poetic form to check against"),
):
    """Validate a poem against form constraints."""
    # Get poem lines
    if file:
        if not file.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(1)
        lines = file.read_text().strip().split("\n")
    elif text:
        lines = [line.strip() for line in text.split("/")]
    else:
        console.print("[red]Provide either a file or --text[/red]")
        raise typer.Exit(1)
    
    # Get form
    try:
        form_def = get_form(form)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    # Check poem
    analysis = check_poem(lines, form_def)
    console.print(format_analysis(analysis))
    
    if not analysis.passed:
        raise typer.Exit(1)


@app.command()
def interactive(
    form: str = typer.Option("haiku", "--form", "-f", help="Poetic form"),
    theme: str = typer.Option(..., "--theme", "-t", help="Theme or topic"),
    resume: Optional[Path] = typer.Option(None, "--resume", "-r", help="Resume from saved progress"),
):
    """Interactive line-by-line composition mode."""
    from sonnet.interactive import run_interactive, load_progress
    
    try:
        form_def = get_form(form)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    if resume and resume.exists():
        try:
            progress = load_progress(str(resume))
            console.print(f"[green]Resuming from {resume}[/green]")
            form_def = get_form(progress.form_name)
            theme = progress.theme
        except Exception as e:
            console.print(f"[yellow]Could not load progress: {e}[/yellow]")
    
    try:
        lines = run_interactive(form_def, theme)
        console.print("\n[bold]Final poem:[/bold]")
        for line in lines:
            console.print(line)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def forms(
    name: Optional[str] = typer.Argument(None, help="Form name for details"),
    details: bool = typer.Option(False, "--details", "-d", help="Show detailed info"),
):
    """List available poetic forms."""
    if name:
        try:
            form_def = get_form(name)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[bold]{form_def.name}[/bold]")
        console.print(f"Description: {form_def.description}")
        console.print(f"Lines: {form_def.lines}")
        
        if isinstance(form_def.syllables, list):
            console.print(f"Syllables: {form_def.syllables}")
        elif form_def.syllables > 0:
            console.print(f"Syllables per line: {form_def.syllables}")
        
        if form_def.rhyme_scheme:
            console.print(f"Rhyme scheme: {form_def.rhyme_scheme}")
        if form_def.meter:
            console.print(f"Meter: {form_def.meter}")
    else:
        table = Table(title="Available Forms")
        table.add_column("Name", style="cyan")
        table.add_column("Lines", justify="right")
        table.add_column("Description")
        
        for form_name in list_forms():
            form_def = get_form(form_name)
            table.add_row(
                form_name,
                str(form_def.lines),
                form_def.description,
            )
        
        console.print(table)


if __name__ == "__main__":
    app()
