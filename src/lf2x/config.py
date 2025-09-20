"""Core configuration primitives for LF2X."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_OUTPUT_DIR = Path("dist")
CONFIG_FILENAME = "lf2x.yaml"


@dataclass(slots=True, frozen=True)
class LF2XSettings:
    """Container describing LF2X runtime preferences."""

    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_file: Path | None = None
    api_base_url: str | None = None
    api_token: str | None = None

    def resolve_output_dir(self, base_dir: Path | None = None) -> Path:
        """Return the absolute output directory without mutating filesystem."""

        base = base_dir if base_dir is not None else Path.cwd()
        candidate = self.output_dir
        return candidate if candidate.is_absolute() else base / candidate

    def with_overrides(
        self,
        *,
        output_dir: str | Path | None = None,
        config_file: str | Path | None = None,
        api_base_url: str | None = None,
        api_token: str | None = None,
    ) -> LF2XSettings:
        """Create a new settings instance overriding selected attributes."""

        return LF2XSettings(
            output_dir=_coerce_path(output_dir, default=self.output_dir),
            config_file=_coerce_optional_path(config_file, default=self.config_file),
            api_base_url=_coerce_optional_str(api_base_url, default=self.api_base_url),
            api_token=_coerce_optional_str(api_token, default=self.api_token),
        )

    @classmethod
    def from_sources(
        cls,
        *,
        output_dir: str | Path | None = None,
        config_file: str | Path | None = None,
        search_paths: Iterable[Path] | None = None,
        api_base_url: str | None = None,
        api_token: str | None = None,
    ) -> LF2XSettings:
        """Build settings from CLI/config inputs using deterministic precedence."""

        resolved_config = _select_config_path(config_file, search_paths)
        config_data = _load_config(resolved_config) if resolved_config else {}

        config_output_dir = _config_output_dir(config_data)
        resolved_output_dir = _coerce_path(
            output_dir,
            default=config_output_dir if config_output_dir is not None else DEFAULT_OUTPUT_DIR,
        )

        resolved_api_base = (
            api_base_url if api_base_url is not None else _config_api_base_url(config_data)
        )
        resolved_api_token = api_token if api_token is not None else _config_api_token(config_data)

        return cls(
            output_dir=resolved_output_dir,
            config_file=resolved_config,
            api_base_url=resolved_api_base,
            api_token=resolved_api_token,
        )


def _coerce_path(value: str | Path | None, *, default: Path) -> Path:
    if value is None:
        return default
    return Path(value)


def _coerce_optional_path(value: str | Path | None, *, default: Path | None) -> Path | None:
    if value is None:
        return default
    return Path(value)


def _coerce_optional_str(value: str | None, *, default: str | None) -> str | None:
    return value if value is not None else default


def _select_config_path(
    config_file: str | Path | None,
    search_paths: Iterable[Path] | None,
) -> Path | None:
    if config_file is not None:
        return Path(config_file)
    if search_paths is None:
        return None
    for location in search_paths:
        candidate = location / CONFIG_FILENAME
        if candidate.exists():
            return candidate
    return None


def _load_config(config_path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Failed to parse configuration file {config_path}") from exc
    if data is None:
        return {}
    if not isinstance(data, Mapping):
        raise ValueError(f"Configuration file {config_path} must contain a mapping")
    return dict(data)


def _config_output_dir(data: Mapping[str, Any]) -> Path | None:
    paths_section = data.get("paths")
    if isinstance(paths_section, Mapping):
        raw = paths_section.get("output_dir")
        if raw is not None:
            return Path(str(raw))
    return None


def _config_api_base_url(data: Mapping[str, Any]) -> str | None:
    api_section = data.get("api")
    if isinstance(api_section, Mapping):
        raw = api_section.get("base_url")
        if raw is not None:
            return str(raw)
    return None


def _config_api_token(data: Mapping[str, Any]) -> str | None:
    api_section = data.get("api")
    if isinstance(api_section, Mapping):
        raw = api_section.get("token")
        if raw is not None:
            return str(raw)
    return None


__all__ = ["DEFAULT_OUTPUT_DIR", "LF2XSettings", "CONFIG_FILENAME"]
