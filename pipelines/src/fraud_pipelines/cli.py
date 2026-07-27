"""Setup-phase pipeline CLI."""

import typer

from fraud_pipelines.config import get_pipeline_settings

app = typer.Typer(no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the pipeline package version."""
    typer.echo("0.1.0")


@app.command("show-config")
def show_config() -> None:
    """Print non-secret reproducibility settings."""
    typer.echo(get_pipeline_settings().model_dump_json())
