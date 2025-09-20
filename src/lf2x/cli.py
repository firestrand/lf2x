"""Typer-based command line entry point."""

from pathlib import Path

import typer
from typer.models import OptionInfo

from . import DEFAULT_OUTPUT_DIR, LF2XSettings, __version__
from .converter import convert_flow

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

    if isinstance(config, OptionInfo):
        config_override: str | None = None
    else:
        config_override = config or None

    config_path = Path(config_override) if config_override else None
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


@app.command()
def convert(
    source: str = typer.Argument(..., help="Path to a LangFlow JSON export"),
    output_dir: str = typer.Option(
        str(DEFAULT_OUTPUT_DIR),
        "--output-dir",
        help="Directory where generated artifacts will be written",
        show_default=True,
    ),
    config: str = typer.Option(
        "",
        "--config",
        help="Optional path to lf2x.yaml configuration file",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Allow overwriting existing files when regenerating projects",
    ),
) -> None:
    """Convert a LangFlow export into a code project."""

    output_override: str | None
    if isinstance(output_dir, OptionInfo):
        output_override = None
    else:
        output_override = output_dir

    if isinstance(config, OptionInfo):
        config_override: str | None = None
    else:
        config_override = config or None

    config_path = Path(config_override) if config_override else None
    search_paths = _derive_search_paths(config_path)
    settings = LF2XSettings.from_sources(
        output_dir=output_override,
        config_file=config_path,
        search_paths=search_paths,
    )

    result = convert_flow(source, settings=settings, overwrite=overwrite)
    typer.echo(f"flow_id={result.flow_id}")
    typer.echo(f"target={result.target.value}")
    typer.echo(f"project_root={result.project_root}")
    typer.echo(f"package={result.package_name}")
    created = sum(1 for entry in result.writes if entry.status in {"created", "would-create"})
    updated = sum(1 for entry in result.writes if entry.status in {"updated", "would-update"})
    typer.echo(f"files_created={created}")
    typer.echo(f"files_updated={updated}")
    typer.echo(f"report_markdown={result.report_markdown}")
    typer.echo(f"report_json={result.report_json}")


if __name__ == "__main__":
    app()
