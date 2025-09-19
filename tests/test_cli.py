from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture

from lf2x.__about__ import __version__
from lf2x.cli import configure, version
from lf2x.config import DEFAULT_OUTPUT_DIR


def test_version_function_outputs_version(capsys: CaptureFixture[str]) -> None:
    version()
    captured = capsys.readouterr()
    assert captured.out.strip() == __version__


def test_configure_function_uses_defaults(capsys: CaptureFixture[str]) -> None:
    configure(output_dir=str(DEFAULT_OUTPUT_DIR), config="")
    captured = capsys.readouterr()
    stdout = captured.out.splitlines()
    resolved = Path(stdout[0].split("=", maxsplit=1)[1])
    assert resolved.name == DEFAULT_OUTPUT_DIR.name
    assert stdout[1] == "config_file=<none>"


def test_configure_function_handles_explicit_config(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    config_file = tmp_path / "lf2x.yaml"
    config_file.write_text("flows: []\n")
    output_dir = tmp_path / "dist"
    configure(output_dir=str(output_dir), config=str(config_file))
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert f"output_dir={output_dir}" in lines
    assert f"config_file={config_file}" in lines
