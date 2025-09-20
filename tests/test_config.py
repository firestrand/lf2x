from __future__ import annotations

from pathlib import Path

import yaml

from lf2x.config import DEFAULT_OUTPUT_DIR, LF2XSettings


def test_from_sources_defaults(tmp_path: Path) -> None:
    settings = LF2XSettings.from_sources()
    assert settings.output_dir == DEFAULT_OUTPUT_DIR
    assert settings.config_file is None
    resolved = settings.resolve_output_dir(base_dir=tmp_path)
    assert resolved == tmp_path / DEFAULT_OUTPUT_DIR


def test_with_overrides_updates_values(tmp_path: Path) -> None:
    base = LF2XSettings(output_dir=tmp_path / "base", api_base_url="https://api", api_token="abc")
    updated = base.with_overrides(
        output_dir="alt",
        config_file=tmp_path / "cfg.yaml",
        api_base_url="https://override",
        api_token="xyz",
    )
    assert updated.output_dir == Path("alt")
    assert updated.config_file == tmp_path / "cfg.yaml"
    assert updated.api_base_url == "https://override"
    assert updated.api_token == "xyz"
    # ensure resolve uses new paths while keeping relative directories isolated
    assert updated.resolve_output_dir(base_dir=tmp_path) == tmp_path / "alt"


def test_from_sources_discovers_config_file(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "lf2x.yaml"
    config_file.write_text("test: true\n")
    settings = LF2XSettings.from_sources(search_paths=[config_dir])
    assert settings.config_file == config_file


def test_from_sources_prefers_explicit_config(tmp_path: Path) -> None:
    explicit = tmp_path / "custom.yaml"
    explicit.write_text("custom: true\n")
    settings = LF2XSettings.from_sources(config_file=explicit, search_paths=[tmp_path])
    assert settings.config_file == explicit


def test_with_overrides_keeps_defaults(tmp_path: Path) -> None:
    base = LF2XSettings()
    updated = base.with_overrides()
    assert updated.output_dir == DEFAULT_OUTPUT_DIR
    assert updated.config_file is None
    assert updated.api_base_url is None
    assert updated.api_token is None


def test_resolve_output_dir_behaviour(tmp_path: Path) -> None:
    candidates: list[Path | None] = [None, Path("./relative"), Path("/absolute")]
    for candidate in candidates:
        settings = LF2XSettings.from_sources(output_dir=candidate)
        resolved = settings.resolve_output_dir(base_dir=tmp_path)
        if candidate is None:
            assert resolved == tmp_path / DEFAULT_OUTPUT_DIR
        elif candidate.is_absolute():
            assert resolved == candidate
        else:
            assert resolved == tmp_path / candidate


def test_from_sources_loads_yaml_configuration(tmp_path: Path) -> None:
    config_path = tmp_path / "lf2x.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {"output_dir": "configured"},
                "api": {"base_url": "https://langflow.local", "token": "abc123"},
            }
        )
    )
    settings = LF2XSettings.from_sources(search_paths=[tmp_path])
    assert settings.resolve_output_dir(base_dir=tmp_path) == tmp_path / "configured"
    assert settings.api_base_url == "https://langflow.local"
    assert settings.api_token == "abc123"
    assert settings.config_file == config_path


def test_cli_overrides_config_file_values(tmp_path: Path) -> None:
    config_path = tmp_path / "lf2x.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "paths": {"output_dir": "configured"},
                "api": {"base_url": "https://config", "token": "config"},
            }
        )
    )
    settings = LF2XSettings.from_sources(
        output_dir="cli-dir",
        config_file=config_path,
        search_paths=[tmp_path],
    )
    assert settings.output_dir == Path("cli-dir")
    assert settings.resolve_output_dir(base_dir=tmp_path) == tmp_path / "cli-dir"
    assert settings.api_base_url == "https://config"
    assert settings.api_token == "config"
    assert settings.config_file == config_path
