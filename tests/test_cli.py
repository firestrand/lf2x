from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from _pytest.capture import CaptureFixture

from lf2x.__about__ import __version__
from lf2x.cli import analyze, configure, convert, validate, version
from lf2x.config import DEFAULT_OUTPUT_DIR


def _output_to_dict(text: str) -> dict[str, str]:
    return dict(line.split("=", maxsplit=1) for line in text.splitlines() if "=" in line)


def test_version_function_outputs_version(capsys: CaptureFixture[str]) -> None:
    version()
    captured = capsys.readouterr()
    assert captured.out.strip() == __version__


def test_configure_function_uses_defaults(capsys: CaptureFixture[str]) -> None:
    configure()
    captured = capsys.readouterr()
    data = _output_to_dict(captured.out)
    resolved = Path(data["output_dir"])
    assert resolved.name == DEFAULT_OUTPUT_DIR.name
    assert data["config_file"] == "<none>"
    assert data["api_base_url"] == "<none>"
    assert data["api_token"] == "<none>"


def test_configure_function_handles_explicit_config(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    config_file = tmp_path / "lf2x.yaml"
    config_file.write_text("flows: []\n")
    output_dir = tmp_path / "dist"
    configure(output_dir=str(output_dir), config=str(config_file))
    captured = capsys.readouterr()
    data = _output_to_dict(captured.out)
    assert data["output_dir"] == str(output_dir)
    assert data["config_file"] == str(config_file)
    assert data["api_base_url"] == "<none>"
    assert data["api_token"] == "<none>"


def test_configure_loads_config_file_values(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    config_file = tmp_path / "lf2x.yaml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "paths": {"output_dir": "configured"},
                "api": {"base_url": "https://config", "token": "secret"},
            }
        )
    )
    configure(config=str(config_file))
    data = _output_to_dict(capsys.readouterr().out)
    assert data["output_dir"].endswith("configured")
    assert data["config_file"] == str(config_file)
    assert data["api_base_url"] == "https://config"
    assert data["api_token"] == "<provided>"


def test_convert_generates_project(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    fixture = Path(__file__).parent / "fixtures" / "flows" / "simple_passthrough.json"
    output_dir = tmp_path / "out"

    convert(source=str(fixture), output_dir=str(output_dir))

    data = _output_to_dict(capsys.readouterr().out)
    assert data["target"] == "langchain"
    project_root = Path(data["project_root"])
    assert project_root.exists()
    assert project_root.is_dir()
    assert project_root.parent == output_dir
    assert (project_root / "pyproject.toml").exists()
    assert "package" in data
    assert "files_created" in data
    assert "files_updated" in data
    assert (project_root / ".env.example").exists()
    assert Path(data["report_markdown"]).exists()
    assert Path(data["report_json"]).exists()


def test_convert_uses_default_output_dir(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = Path(__file__).parent / "fixtures" / "flows" / "simple_passthrough.json"
    monkeypatch.chdir(tmp_path)

    convert(source=str(fixture))

    data = _output_to_dict(capsys.readouterr().out)
    project_root = Path(data["project_root"])
    assert project_root.parent == tmp_path / DEFAULT_OUTPUT_DIR
    assert (project_root / "pyproject.toml").exists()
    assert "package" in data
    assert (project_root / ".env.example").exists()
    assert Path(data["report_markdown"]).exists()
    assert Path(data["report_json"]).exists()


def test_analyze_reports_flow_characteristics(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    fixture = Path(__file__).parent / "fixtures" / "flows" / "simple_passthrough.json"

    analyze(source=str(fixture))

    data = _output_to_dict(capsys.readouterr().out)
    assert data["pattern"] == "linear"
    assert data["recommended_target"] == "langchain"
    assert data["node_count"] == "2"
    assert data["edge_count"] == "1"


def test_validate_confirms_flow_is_valid(capsys: CaptureFixture[str]) -> None:
    fixture = Path(__file__).parent / "fixtures" / "flows" / "simple_passthrough.json"

    validate(source=str(fixture))

    data = _output_to_dict(capsys.readouterr().out)
    assert data["valid"] == "true"
    assert data["recommended_target"] == "langchain"
