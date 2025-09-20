"""Intermediate Representation for LangFlow to X (LF2X)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .parser import LangFlowDocument


@dataclass(frozen=True, slots=True)
class IRNode:
    """Normalized representation of a graph node."""

    node_id: str
    type: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class IREdge:
    """Normalized representation of a graph edge."""

    edge_id: str
    source: str
    target: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class IRMetadata:
    """Metadata describing the origin and destinations of the IR."""

    source_path: Path
    output_dir: Path


@dataclass(frozen=True, slots=True)
class IntermediateRepresentation:
    """Aggregated LangFlow graph ready for analysis/generation."""

    flow_id: str
    name: str
    version: str
    nodes: tuple[IRNode, ...]
    edges: tuple[IREdge, ...]
    metadata: IRMetadata

    def node_ids(self) -> set[str]:
        """Return a set of node identifiers."""

        return {node.node_id for node in self.nodes}

    def edge_ids(self) -> set[str]:
        """Return a set of edge identifiers."""

        return {edge.edge_id for edge in self.edges}


def build_intermediate_representation(
    document: LangFlowDocument,
) -> IntermediateRepresentation:
    """Construct an IR from a parsed LangFlow document."""

    nodes = tuple(IRNode(node.node_id, node.type, dict(node.data)) for node in document.nodes)
    edges = tuple(
        IREdge(edge.edge_id, edge.source, edge.target, dict(edge.data)) for edge in document.edges
    )
    metadata = IRMetadata(
        source_path=document.metadata.source_path,
        output_dir=document.metadata.output_dir,
    )
    return IntermediateRepresentation(
        flow_id=document.flow_id,
        name=document.name,
        version=document.version,
        nodes=nodes,
        edges=edges,
        metadata=metadata,
    )


__all__ = [
    "IRNode",
    "IREdge",
    "IRMetadata",
    "IntermediateRepresentation",
    "build_intermediate_representation",
]
