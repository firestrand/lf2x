"""Utilities for parsing LangFlow JSON exports into LF2X documents."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import LF2XSettings
from .langflow_schema import LangFlowEdgePayload, LangFlowExport, LangFlowNodePayload

SUPPORTED_VERSIONS: Sequence[str] = ("1.0.0", "1.5.1")


class UnsupportedFlowVersionError(ValueError):
    """Raised when an exported flow uses an unsupported schema version."""


@dataclass(frozen=True, slots=True)
class FlowMetadata:
    """Metadata describing the parsed flow and associated artifacts."""

    source_path: Path
    output_dir: Path


@dataclass(frozen=True, slots=True)
class FlowNode:
    """A single LangFlow node representation."""

    node_id: str
    type: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class FlowEdge:
    """A single LangFlow edge representation."""

    edge_id: str
    source: str
    target: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LangFlowDocument:
    """Structured representation of a LangFlow export."""

    flow_id: str
    name: str
    version: str
    nodes: tuple[FlowNode, ...]
    edges: tuple[FlowEdge, ...]
    metadata: FlowMetadata


def parse_langflow_json(
    source: Path | str,
    *,
    settings: LF2XSettings | None = None,
    supported_versions: Sequence[str] = SUPPORTED_VERSIONS,
    encoding: str = "utf-8",
) -> LangFlowDocument:
    """Parse a LangFlow JSON export file."""

    path = Path(source)
    payload = json.loads(path.read_text(encoding=encoding))

    export = LangFlowExport.from_mapping(payload)
    if supported_versions and export.version not in supported_versions:
        message = (
            "Unsupported LangFlow version '"
            f"{export.version}'. Supported: {', '.join(supported_versions)}"
        )
        raise UnsupportedFlowVersionError(message)

    nodes = tuple(_convert_node(node) for node in export.nodes)
    edges = tuple(_convert_edge(edge) for edge in export.edges)

    output_settings = settings or LF2XSettings()
    output_dir = output_settings.resolve_output_dir()

    metadata = FlowMetadata(source_path=path, output_dir=output_dir)

    return LangFlowDocument(
        flow_id=export.flow_id,
        name=export.name,
        version=export.version,
        nodes=nodes,
        edges=edges,
        metadata=metadata,
    )


def _convert_node(payload: LangFlowNodePayload) -> FlowNode:
    return FlowNode(node_id=payload.node_id, type=payload.type, data=dict(payload.data))


def _convert_edge(payload: LangFlowEdgePayload) -> FlowEdge:
    return FlowEdge(
        edge_id=payload.edge_id,
        source=payload.source,
        target=payload.target,
        data=dict(payload.data),
    )


__all__ = [
    "LangFlowDocument",
    "FlowEdge",
    "FlowMetadata",
    "FlowNode",
    "UnsupportedFlowVersionError",
    "parse_langflow_json",
]
