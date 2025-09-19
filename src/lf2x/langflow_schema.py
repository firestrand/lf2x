"""LangFlow export schema helpers.

This module adapts the LangFlow dataflow schema from
https://github.com/langflow-ai/langflow (MIT License). The original models are
Pydantic-based; here we provide lightweight dataclass equivalents for LF2X while
preserving the relevant field names.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LangFlowEdgePayload:
    """Edge entry from a LangFlow export."""

    edge_id: str
    source: str
    target: str
    data: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> LangFlowEdgePayload:
        edge_id = _stringify(_require(mapping, "id"))
        source = _stringify(_require(mapping, "source"))
        target = _stringify(_require(mapping, "target"))

        data = mapping.get("data", {}) or {}
        if not isinstance(data, Mapping):
            raise ValueError("Edge 'data' must be a mapping if provided")

        return cls(edge_id=edge_id, source=source, target=target, data=data)


@dataclass(frozen=True)
class LangFlowNodePayload:
    """Node entry from a LangFlow export."""

    node_id: str
    type: str
    data: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> LangFlowNodePayload:
        node_id = _stringify(_require(mapping, "id"))
        data = mapping.get("data", {}) or {}
        if not isinstance(data, Mapping):
            raise ValueError("Node 'data' must be a mapping if provided")

        raw_type = mapping.get("type") or data.get("type")
        if raw_type is None:
            raise ValueError("Node entries must include 'type'")

        return cls(node_id=node_id, type=_stringify(raw_type), data=data)


@dataclass(frozen=True)
class LangFlowGraphPayload:
    """Container for nodes and edges stored under the ``data`` key."""

    nodes: Sequence[LangFlowNodePayload]
    edges: Sequence[LangFlowEdgePayload]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> LangFlowGraphPayload:
        return cls(
            nodes=_coerce_nodes(mapping.get("nodes")),
            edges=_coerce_edges(mapping.get("edges")),
        )


@dataclass(frozen=True)
class LangFlowExport:
    """Top-level LangFlow export document."""

    flow_id: str
    name: str
    description: str | None
    tags: Sequence[str]
    version: str
    nodes: Sequence[LangFlowNodePayload]
    edges: Sequence[LangFlowEdgePayload]

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> LangFlowExport:
        flow_id = _stringify(_require(mapping, "id"))
        name = _stringify(_require(mapping, "name"))
        description = mapping.get("description")
        tags_raw = mapping.get("tags") or []
        if not isinstance(tags_raw, Sequence) or isinstance(tags_raw, str | bytes):
            raise ValueError("'tags' must be a sequence if provided")
        tags = [_stringify(tag) for tag in tags_raw]

        version = mapping.get("version") or mapping.get("last_tested_version")
        if version is None:
            raise ValueError("Missing required field 'version'")

        nodes_raw = mapping.get("nodes")
        edges_raw = mapping.get("edges")
        if nodes_raw is None or edges_raw is None:
            data_block = mapping.get("data")
            if isinstance(data_block, Mapping):
                graph = LangFlowGraphPayload.from_mapping(data_block)
                nodes_raw = nodes_raw or graph.nodes
                edges_raw = edges_raw or graph.edges

        nodes = _coerce_nodes(nodes_raw)
        edges = _coerce_edges(edges_raw)

        return cls(
            flow_id=flow_id,
            name=name,
            description=_stringify(description) if description is not None else None,
            tags=tags,
            version=_stringify(version),
            nodes=nodes,
            edges=edges,
        )


def _coerce_nodes(raw: Any) -> Sequence[LangFlowNodePayload]:
    if isinstance(raw, Sequence) and not isinstance(raw, str | bytes):
        result: list[LangFlowNodePayload] = []
        for item in raw:
            if isinstance(item, LangFlowNodePayload):
                result.append(item)
            else:
                result.append(LangFlowNodePayload.from_mapping(item))
        return result
    raise ValueError("'nodes' must be a list")


def _coerce_edges(raw: Any) -> Sequence[LangFlowEdgePayload]:
    if isinstance(raw, Sequence) and not isinstance(raw, str | bytes):
        result: list[LangFlowEdgePayload] = []
        for item in raw:
            if isinstance(item, LangFlowEdgePayload):
                result.append(item)
            else:
                result.append(LangFlowEdgePayload.from_mapping(item))
        return result
    raise ValueError("'edges' must be a list")


def _require(mapping: Mapping[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required field '{key}'")
    return mapping[key]


def _stringify(value: Any) -> str:
    return str(value)


__all__ = [
    "LangFlowEdgePayload",
    "LangFlowExport",
    "LangFlowGraphPayload",
    "LangFlowNodePayload",
]
