from __future__ import annotations

from pathlib import Path

from lf2x.config import LF2XSettings
from lf2x.ir import (
    IntermediateRepresentation,
    IREdge,
    IRMetadata,
    IRNode,
    build_intermediate_representation,
)
from lf2x.parser import parse_langflow_json

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "flows"


def test_build_ir_from_parsed_document(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "simple_passthrough.json"
    settings = LF2XSettings.from_sources(output_dir=tmp_path / "out")

    document = parse_langflow_json(fixture, settings=settings)
    ir = build_intermediate_representation(document)

    assert isinstance(ir, IntermediateRepresentation)
    assert ir.flow_id == document.flow_id
    assert ir.name == document.name
    assert ir.version == document.version
    assert len(ir.nodes) == len(document.nodes)
    assert len(ir.edges) == len(document.edges)
    assert ir.metadata == IRMetadata(
        source_path=document.metadata.source_path,
        output_dir=document.metadata.output_dir,
    )


def test_ir_nodes_and_edges_are_copies(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "simple_passthrough.json"

    document = parse_langflow_json(fixture)
    ir = build_intermediate_representation(document)

    assert all(isinstance(node, IRNode) for node in ir.nodes)
    assert all(isinstance(edge, IREdge) for edge in ir.edges)

    # Ensure dictionaries are copied, not referenced
    for doc_node, ir_node in zip(document.nodes, ir.nodes, strict=True):
        assert doc_node.data == ir_node.data
        assert doc_node.data is not ir_node.data
    for doc_edge, ir_edge in zip(document.edges, ir.edges, strict=True):
        assert doc_edge.data == ir_edge.data
        assert doc_edge.data is not ir_edge.data


def test_ir_helper_methods(tmp_path: Path) -> None:
    document = parse_langflow_json(FIXTURE_DIR / "simple_passthrough.json")
    ir = build_intermediate_representation(document)

    assert ir.node_ids() == {node.node_id for node in ir.nodes}
    assert ir.edge_ids() == {edge.edge_id for edge in ir.edges}
