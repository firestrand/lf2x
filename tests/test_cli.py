from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from _pytest.capture import CaptureFixture

from lf2x.__about__ import __version__
from lf2x.cli import configure, convert, version
from lf2x.config import DEFAULT_OUTPUT_DIR


def test_version_function_outputs_version(capsys: CaptureFixture[str]) -> None:
    version()
    captured = capsys.readouterr()
    assert captured.out.strip() == __version__


def test_configure_function_uses_defaults(capsys: CaptureFixture[str]) -> None:
    configure()
    captured = capsys.readouterr()
    stdout = captured.out.splitlines()
    resolved = Path(stdout[0].split("=", maxsplit=1)[1])
    assert resolved.name == DEFAULT_OUTPUT_DIR.name
    assert stdout[1] == "config_file=<none>"
    assert stdout[2] == "api_base_url=<none>"
    assert stdout[3] == "api_token=<none>"


def test_configure_function_handles_explicit_config(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    config_file = tmp_path / "lf2x.yaml"
    config_file.write_text("flows: []\n")
    output_dir = tmp_path / "dist"
    configure(output_dir=str(output_dir), config=str(config_file))
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == f"output_dir={output_dir}"
    assert lines[1] == f"config_file={config_file}"
    assert lines[2] == "api_base_url=<none>"
    assert lines[3] == "api_token=<none>"


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
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].endswith("configured")
    assert lines[1] == f"config_file={config_file}"
    assert lines[2] == "api_base_url=https://config"
    assert lines[3] == "api_token=<provided>"


def test_convert_generates_project(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    fixture = Path(__file__).parent / "fixtures" / "flows" / "simple_passthrough.json"
    output_dir = tmp_path / "out"

    convert(source=str(fixture), output_dir=str(output_dir))

    lines = capsys.readouterr().out.splitlines()
    data = dict(line.split("=", maxsplit=1) for line in lines)
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

    lines = capsys.readouterr().out.splitlines()
    data = dict(line.split("=", maxsplit=1) for line in lines)
    project_root = Path(data["project_root"])
    assert project_root.parent == tmp_path / DEFAULT_OUTPUT_DIR
    assert (project_root / "pyproject.toml").exists()
    assert "package" in data
    assert (project_root / ".env.example").exists()
    assert Path(data["report_markdown"]).exists()
    assert Path(data["report_json"]).exists()
