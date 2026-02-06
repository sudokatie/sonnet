"""CLI entry point for Sonnet."""

import typer

app = typer.Typer(
    name="sonnet",
    help="Constraint-based poetry generator. Rules breed creativity.",
)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """Sonnet: Generate poetry that respects form."""
    if version:
        from sonnet import __version__
        typer.echo(f"sonnet {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
