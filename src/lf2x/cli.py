"""Typer-based command line entry point."""

from pathlib import Path

import typer
from typer.models import OptionInfo

from . import DEFAULT_OUTPUT_DIR, LF2XSettings, __version__
from .analyzer import analyze_flow
from .converter import convert_flow
from .ir import build_intermediate_representation
from .parser import parse_langflow_json

app = typer.Typer(add_completion=False, help="LangFlow to X (LF2X) developer tools")


def _derive_search_paths(config_path: Path | None) -> list[Path] | None:
    if config_path is None:
        return None
    parent = config_path.parent if config_path.suffix else config_path
    return [parent, Path.cwd()]


def _normalize_option(value: str | OptionInfo | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, OptionInfo):
        return None
    return value or None


def _build_settings(*, output_value: str | None, config_value: str | None) -> LF2XSettings:
    config_path = Path(config_value) if config_value else None
    search_paths = _derive_search_paths(config_path)
    return LF2XSettings.from_sources(
        output_dir=output_value,
        config_file=config_path,
        search_paths=search_paths,
    )


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

    output_override = _normalize_option(output_dir)
    config_override = _normalize_option(config)
    settings = _build_settings(output_value=output_override, config_value=config_override)
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

    output_override = _normalize_option(output_dir)
    config_override = _normalize_option(config)
    settings = _build_settings(output_value=output_override, config_value=config_override)

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


@app.command()
def analyze(
    source: str = typer.Argument(..., help="Path to a LangFlow JSON export"),
    output_dir: str = typer.Option(
        str(DEFAULT_OUTPUT_DIR),
        "--output-dir",
        help="Output directory used to resolve IR metadata",
        show_default=True,
    ),
    config: str = typer.Option(
        "",
        "--config",
        help="Optional path to lf2x.yaml configuration file",
    ),
) -> None:
    """Analyze a LangFlow export and report structural characteristics."""

    output_override = _normalize_option(output_dir)
    config_override = _normalize_option(config)
    settings = _build_settings(output_value=output_override, config_value=config_override)
    document = parse_langflow_json(source, settings=settings)
    ir = build_intermediate_representation(document)
    analysis = analyze_flow(ir)
    typer.echo(f"flow_id={ir.flow_id}")
    typer.echo(f"name={ir.name}")
    typer.echo(f"pattern={analysis.pattern.name.lower()}")
    typer.echo(f"recommended_target={analysis.recommended_target.value}")
    typer.echo(f"has_cycles={str(analysis.has_cycles).lower()}")
    typer.echo(f"has_branching={str(analysis.has_branching).lower()}")
    typer.echo(f"node_count={len(ir.nodes)}")
    typer.echo(f"edge_count={len(ir.edges)}")
    typer.echo(f"output_dir={settings.resolve_output_dir()}")


@app.command()
def validate(
    source: str = typer.Argument(..., help="Path to a LangFlow JSON export"),
    config: str = typer.Option(
        "",
        "--config",
        help="Optional path to lf2x.yaml configuration file",
    ),
) -> None:
    """Validate that a LangFlow export can be parsed and analyzed."""

    config_override = _normalize_option(config)
    settings = _build_settings(output_value=None, config_value=config_override)
    document = parse_langflow_json(source, settings=settings)
    ir = build_intermediate_representation(document)
    analysis = analyze_flow(ir)
    typer.echo(f"flow_id={ir.flow_id}")
    typer.echo("valid=true")
    typer.echo(f"node_count={len(ir.nodes)}")
    typer.echo(f"edge_count={len(ir.edges)}")
    typer.echo(f"recommended_target={analysis.recommended_target.value}")


if __name__ == "__main__":
    app()
