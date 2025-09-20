from __future__ import annotations

from pathlib import Path

from lf2x.analyzer import FlowPattern, TargetRecommendation, analyze_flow
from lf2x.ir import (
    IntermediateRepresentation,
    IREdge,
    IRMetadata,
    IRNode,
    build_intermediate_representation,
)
from lf2x.parser import parse_langflow_json

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "flows"


def _build_ir(fixture_name: str) -> IntermediateRepresentation:
    document = parse_langflow_json(FIXTURE_DIR / fixture_name)
    return build_intermediate_representation(document)


def test_analyze_flow_linear_recommends_langchain() -> None:
    ir = _build_ir("simple_passthrough.json")

    analysis = analyze_flow(ir)

    assert analysis.pattern is FlowPattern.LINEAR
    assert analysis.recommended_target is TargetRecommendation.LANGCHAIN
    assert analysis.has_cycles is False
    assert analysis.has_branching is False


def test_analyze_flow_branching_recommends_langgraph() -> None:
    ir = _build_ir("price_deal_finder.json")

    analysis = analyze_flow(ir)

    assert analysis.pattern is FlowPattern.BRANCHING
    assert analysis.recommended_target is TargetRecommendation.LANGGRAPH
    assert analysis.has_branching is True
    assert analysis.has_cycles is False


def test_analyze_flow_detects_cycles() -> None:
    nodes = (
        IRNode("start", "Start", {}),
        IRNode("middle", "Middle", {}),
        IRNode("end", "End", {}),
    )
    edges = (
        IREdge("e1", "start", "middle", {}),
        IREdge("e2", "middle", "end", {}),
        IREdge("e3", "end", "middle", {}),
    )
    ir = IntermediateRepresentation(
        flow_id="cyclic",
        name="Cyclic",
        version="1.0.0",
        nodes=nodes,
        edges=edges,
        metadata=IRMetadata(
            source_path=Path("cyclic.json"),
            output_dir=Path("dist"),
        ),
    )

    analysis = analyze_flow(ir)

    assert analysis.pattern is FlowPattern.CYCLIC
    assert analysis.recommended_target is TargetRecommendation.LANGGRAPH
    assert analysis.has_cycles is True
