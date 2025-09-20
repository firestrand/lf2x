"""Typer-based command line entry point."""

from pathlib import Path

import typer
from typer.models import OptionInfo

from . import DEFAULT_OUTPUT_DIR, LF2XSettings, __version__

app = typer.Typer(add_completion=False, help="LangFlow to X (LF2X) developer tools")


def _derive_search_paths(config_path: Path | None) -> list[Path] | None:
    if config_path is None:
        return None
    parent = config_path.parent if config_path.suffix else config_path
    return [parent, Path.cwd()]


@app.command()
def version() -> None:
    """Print the installed LF2X version."""

    typer.echo(__version__)


@app.command()
def configure(
    output_dir: str = typer.Option(
        str(DEFAULT_OUTPUT_DIR),
        "--output-dir",
        help="Directory for generated artifacts",
        show_default=True,
    ),
    config: str = typer.Option(
        "",
        "--config",
        help="Optional path to lf2x.yaml configuration file",
    ),
) -> None:
    """Show the resolved configuration for the current invocation."""

    output_override: str | None
    if isinstance(output_dir, OptionInfo):
        output_override = None
    else:
        output_override = output_dir

    config_path = Path(config) if config else None
    search_paths = _derive_search_paths(config_path)
    settings = LF2XSettings.from_sources(
        output_dir=output_override,
        config_file=config_path,
        search_paths=search_paths,
    )
    resolved_dir = settings.resolve_output_dir()
    typer.echo(f"output_dir={resolved_dir}")
    typer.echo(
        f"config_file={settings.config_file}" if settings.config_file else "config_file=<none>"
    )
    typer.echo(f"api_base_url={settings.api_base_url or '<none>'}")
    typer.echo("api_token=<provided>" if settings.api_token else "api_token=<none>")


if __name__ == "__main__":
    app()
