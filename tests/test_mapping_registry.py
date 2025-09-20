from __future__ import annotations

from pathlib import Path

import pytest

from lf2x.mapping_registry import ComponentMapping, ComponentRegistry, load_registry


def test_registry_loads_default_path() -> None:
    registry = load_registry()

    mapping = registry.get("ChatInput")

    assert isinstance(mapping, ComponentMapping)
    assert mapping.supported is True
    assert mapping.target == "langchain"


def test_registry_support_checks() -> None:
    registry = load_registry()

    assert registry.is_supported("ChatOutput") is True
    assert registry.is_supported("UnknownComponent") is False


def test_registry_target_recommendation() -> None:
    registry = load_registry()

    assert registry.suggested_target("Agent") == "langgraph"
    assert registry.suggested_target("UnknownComponent") is None


def test_registry_handles_partial_support(tmp_path: Path) -> None:
    registry_path = tmp_path / "components.yaml"
    registry_path.write_text(
        """
- type: PartialComponent
  supported: false
  target: langchain
  notes: Needs manual intervention
"""
    )
    registry = ComponentRegistry(registry_path)

    mapping = registry.get("PartialComponent")
    assert mapping
    assert mapping.supported is False
    assert mapping.notes == "Needs manual intervention"


def test_registry_invalid_format_raises(tmp_path: Path) -> None:
    registry_path = tmp_path / "components.yaml"
    registry_path.write_text("{}\n")

    with pytest.raises(ValueError, match="Invalid component registry format"):
        ComponentRegistry(registry_path)
