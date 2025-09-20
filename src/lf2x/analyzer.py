"""Flow analysis helpers for LF2X."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .ir import IntermediateRepresentation


class FlowPattern(Enum):
    """High-level classification of a LangFlow graph."""

    LINEAR = auto()
    BRANCHING = auto()
    CYCLIC = auto()


class TargetRecommendation(Enum):
    """Suggested downstream target based on flow shape."""

    LANGCHAIN = "langchain"
    LANGGRAPH = "langgraph"


@dataclass(frozen=True, slots=True)
class FlowAnalysis:
    """Summary of the structural characteristics of a flow."""

    pattern: FlowPattern
    recommended_target: TargetRecommendation
    has_cycles: bool
    has_branching: bool


def analyze_flow(ir: IntermediateRepresentation) -> FlowAnalysis:
    """Analyze an Intermediate Representation and classify its flow pattern."""

    adjacency: dict[str, set[str]] = {node.node_id: set() for node in ir.nodes}
    indegree: dict[str, int] = {node.node_id: 0 for node in ir.nodes}

    for edge in ir.edges:
        adjacency.setdefault(edge.source, set()).add(edge.target)
        indegree.setdefault(edge.target, 0)
        indegree.setdefault(edge.source, 0)
        indegree[edge.target] += 1

    has_branching = any(len(targets) > 1 for targets in adjacency.values()) or any(
        degree > 1 for degree in indegree.values()
    )
    has_cycles = _detect_cycle(adjacency)

    if has_cycles:
        pattern = FlowPattern.CYCLIC
        recommendation = TargetRecommendation.LANGGRAPH
    elif has_branching:
        pattern = FlowPattern.BRANCHING
        recommendation = TargetRecommendation.LANGGRAPH
    else:
        pattern = FlowPattern.LINEAR
        recommendation = TargetRecommendation.LANGCHAIN

    return FlowAnalysis(
        pattern=pattern,
        recommended_target=recommendation,
        has_cycles=has_cycles,
        has_branching=has_branching,
    )


def _detect_cycle(graph: dict[str, set[str]]) -> bool:
    visited: set[str] = set()
    stack: set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        stack.add(node)
        for neighbour in graph.get(node, set()):
            if neighbour not in visited:
                if dfs(neighbour):
                    return True
            elif neighbour in stack:
                return True
        stack.remove(node)
        return False

    for node in graph:
        if node not in visited and dfs(node):
            return True
    return False


__all__ = [
    "FlowAnalysis",
    "FlowPattern",
    "TargetRecommendation",
    "analyze_flow",
]
