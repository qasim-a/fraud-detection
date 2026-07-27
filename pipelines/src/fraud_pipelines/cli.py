"""Setup-phase pipeline CLI."""

import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the pipeline package version."""
    typer.echo("0.1.0")
