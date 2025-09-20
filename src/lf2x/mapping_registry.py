"""Component mapping registry for LangFlow to LF2X conversions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent / "mappings" / "components.yaml"
TargetType = Literal["langchain", "langgraph"]


@dataclass(frozen=True, slots=True)
class ComponentMapping:
    """Describes LF2X support for a LangFlow component."""

    type: str
    supported: bool
    target: TargetType
    notes: str | None = None


class ComponentRegistry:
    """Registry of LangFlow component mappings."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or REGISTRY_PATH
        self._entries = self._load()

    def get(self, component_type: str) -> ComponentMapping | None:
        """Return mapping for a given component type, if known."""

        key = component_type.strip()
        return self._entries.get(key)

    def is_supported(self, component_type: str) -> bool:
        entry = self.get(component_type)
        return entry.supported if entry else False

    def suggested_target(self, component_type: str) -> TargetType | None:
        entry = self.get(component_type)
        return entry.target if entry else None

    def _load(self) -> dict[str, ComponentMapping]:
        raw = yaml.safe_load(self._path.read_text())
        if not isinstance(raw, list):
            raise ValueError(f"Invalid component registry format in {self._path}")
        entries: dict[str, ComponentMapping] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            component_type = str(item.get("type"))
            supported = bool(item.get("supported", False))
            target = str(item.get("target"))
            notes = item.get("notes")
            entries[component_type] = ComponentMapping(
                type=component_type,
                supported=supported,
                target=target,  # type: ignore[arg-type]
                notes=str(notes) if notes is not None else None,
            )
        return entries


def load_registry(path: Path | None = None) -> ComponentRegistry:
    return ComponentRegistry(path=path)


__all__ = [
    "ComponentMapping",
    "ComponentRegistry",
    "REGISTRY_PATH",
    "TargetType",
    "load_registry",
]
