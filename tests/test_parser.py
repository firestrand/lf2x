from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest

from lf2x.config import DEFAULT_OUTPUT_DIR, LF2XSettings
from lf2x.parser import LangFlowDocument, UnsupportedFlowVersionError, parse_langflow_json

F = TypeVar("F", bound=Callable[..., Any])


def typed_parametrize(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    return cast(Callable[[F], F], pytest.mark.parametrize(*args, **kwargs))


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "flows"


def test_parse_langflow_json_returns_document(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "simple_passthrough.json"
    target_dir = tmp_path / "artifacts"
    settings = LF2XSettings.from_sources(output_dir=target_dir)

    document = parse_langflow_json(fixture, settings=settings)

    assert isinstance(document, LangFlowDocument)
    assert document.flow_id == "b94bc279-989c-42bb-95ec-6baea451549a"
    assert document.name == "Simple Passthrough"
    assert document.version == "1.5.1"
    assert len(document.nodes) == 2
    assert len(document.edges) == 1
    assert document.metadata.source_path == fixture
    assert document.metadata.output_dir == target_dir


def test_parse_langflow_json_defaults_output_dir_when_not_provided(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "simple_passthrough.json"
    settings = LF2XSettings()  # defaults to dist/

    document = parse_langflow_json(fixture, settings=settings)

    assert document.metadata.output_dir == Path.cwd() / DEFAULT_OUTPUT_DIR


@typed_parametrize("version", ["0.9.0", "2.0.0"])
def test_parse_langflow_json_rejects_unsupported_versions(version: str, tmp_path: Path) -> None:
    fixture = tmp_path / "unsupported.json"
    fixture.write_text(
        json.dumps(
            {
                "id": "flow-legacy",
                "name": "Legacy Flow",
                "last_tested_version": version,
                "data": {
                    "nodes": [],
                    "edges": [],
                },
            }
        )
    )

    with pytest.raises(UnsupportedFlowVersionError, match=version):
        parse_langflow_json(fixture)


@typed_parametrize("missing_field", ["id", "name", "version", "nodes", "edges"])
def test_parse_langflow_json_validates_required_fields(missing_field: str, tmp_path: Path) -> None:
    payload: dict[str, Any] = {
        "id": "flow",
        "name": "Flow",
        "last_tested_version": "1.5.1",
        "data": {
            "nodes": [],
            "edges": [],
        },
    }
    if missing_field in {"nodes", "edges"}:
        payload["data"].pop(missing_field)
    elif missing_field == "version":
        payload.pop("last_tested_version")
    else:
        payload.pop(missing_field)

    fixture = tmp_path / "invalid.json"
    fixture.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match=missing_field):
        parse_langflow_json(fixture)


def test_parse_langflow_json_uses_inner_node_type(tmp_path: Path) -> None:
    payload = {
        "id": "flow",
        "name": "Flow",
        "last_tested_version": "1.5.1",
        "nodes": [
            {
                "id": "node-1",
                "data": {"type": "InnerType"},
            }
        ],
        "edges": [],
    }
    fixture = tmp_path / "inner_type.json"
    fixture.write_text(json.dumps(payload))

    document = parse_langflow_json(fixture)

    node = document.nodes[0]
    assert node.type == "InnerType"


def test_parse_langflow_json_rejects_non_list_nodes(tmp_path: Path) -> None:
    payload = {
        "id": "flow",
        "name": "Flow",
        "last_tested_version": "1.5.1",
        "nodes": {},
        "edges": [],
    }
    fixture = tmp_path / "invalid_nodes.json"
    fixture.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="'nodes' must be a list"):
        parse_langflow_json(fixture)


def test_parse_langflow_json_rejects_invalid_node_data(tmp_path: Path) -> None:
    payload = {
        "id": "flow",
        "name": "Flow",
        "last_tested_version": "1.5.1",
        "nodes": [
            {
                "id": "node-1",
                "type": "Test",
                "data": "not-a-dict",
            }
        ],
        "edges": [],
    }
    fixture = tmp_path / "invalid_node_data.json"
    fixture.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="Node 'data' must be a mapping"):
        parse_langflow_json(fixture)


def test_parse_langflow_json_rejects_invalid_edges(tmp_path: Path) -> None:
    payload = {
        "id": "flow",
        "name": "Flow",
        "last_tested_version": "1.5.1",
        "nodes": [],
        "edges": {},
    }
    fixture = tmp_path / "invalid_edges.json"
    fixture.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="'edges' must be a list"):
        parse_langflow_json(fixture)


def test_parse_langflow_json_rejects_invalid_edge_data(tmp_path: Path) -> None:
    payload = {
        "id": "flow",
        "name": "Flow",
        "last_tested_version": "1.5.1",
        "nodes": [],
        "edges": [
            {
                "id": "edge-1",
                "source": "node-a",
                "target": "node-b",
                "data": "not-a-dict",
            }
        ],
    }
    fixture = tmp_path / "invalid_edge_data.json"
    fixture.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="Edge 'data' must be a mapping"):
        parse_langflow_json(fixture)
