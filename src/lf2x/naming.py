"""Utility helpers for naming generated artifacts."""

from __future__ import annotations

import re

_SLUG_PATTERN = re.compile(r"[^a-z0-9_]")
_UNDERSCORE_RUN = re.compile(r"_+")


def slugify(value: str, *, default: str) -> str:
    """Normalize a string for use in package names and directories."""

    cleaned = value.strip().lower().replace(" ", "_").replace("/", "_")
    cleaned = _SLUG_PATTERN.sub("_", cleaned)
    cleaned = _UNDERSCORE_RUN.sub("_", cleaned).strip("_")
    return cleaned or default


__all__ = ["slugify"]
