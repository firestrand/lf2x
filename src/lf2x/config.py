"""Core configuration primitives for lf2x."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("dist")


@dataclass(slots=True, frozen=True)
class LF2XSettings:
    """Configuration container describing how LF2X should behave."""

    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_file: Path | None = None

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
    ) -> LF2XSettings:
        """Create a new settings object overriding selected attributes."""

        return LF2XSettings(
            output_dir=_coerce_path(output_dir, default=self.output_dir),
            config_file=_coerce_optional_path(config_file, default=self.config_file),
        )

    @classmethod
    def from_sources(
        cls,
        *,
        output_dir: str | Path | None = None,
        config_file: str | Path | None = None,
        search_paths: Iterable[Path] | None = None,
    ) -> LF2XSettings:
        """Build settings from CLI/config inputs using deterministic precedence."""

        resolved_output_dir = _coerce_path(output_dir, default=DEFAULT_OUTPUT_DIR)
        resolved_config = _select_config_path(config_file, search_paths)
        return cls(output_dir=resolved_output_dir, config_file=resolved_config)


def _coerce_path(value: str | Path | None, *, default: Path) -> Path:
    if value is None:
        return default
    candidate = Path(value)
    return candidate


def _coerce_optional_path(value: str | Path | None, *, default: Path | None) -> Path | None:
    if value is None:
        return default
    return Path(value)


def _select_config_path(
    config_file: str | Path | None,
    search_paths: Iterable[Path] | None,
) -> Path | None:
    if config_file is not None:
        return Path(config_file)
    if search_paths is None:
        return None
    for location in search_paths:
        candidate = location / "lf2x.yaml"
        if candidate.exists():
            return candidate
    return None


__all__ = ["DEFAULT_OUTPUT_DIR", "LF2XSettings"]
