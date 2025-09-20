from __future__ import annotations

from pathlib import Path

import pytest

from lf2x.generators.langgraph import LangGraphProject, generate_langgraph_project
from lf2x.ir import IntermediateRepresentation, IREdge, IRMetadata, IRNode


def _make_linear_ir() -> IntermediateRepresentation:
    nodes = (
        IRNode("start", "Start", {}),
        IRNode("end", "End", {}),
    )
    edges = (IREdge("edge", "start", "end", {}),)
    return IntermediateRepresentation(
        flow_id="linear",
        name="Linear",
        version="1.0.0",
        nodes=nodes,
        edges=edges,
        metadata=IRMetadata(Path("linear.json"), Path("dist")),
    )


def _make_branching_ir() -> IntermediateRepresentation:
    nodes = (
        IRNode("start", "Start", {}),
        IRNode("left", "Left", {}),
        IRNode("right", "Right", {}),
        IRNode("end", "End", {}),
    )
    edges = (
        IREdge("e1", "start", "left", {}),
        IREdge("e2", "start", "right", {}),
        IREdge("e3", "left", "end", {}),
        IREdge("e4", "right", "end", {}),
    )
    return IntermediateRepresentation(
        flow_id="branching",
        name="Branching",
        version="1.0.0",
        nodes=nodes,
        edges=edges,
        metadata=IRMetadata(Path("branching.json"), Path("dist")),
    )


def test_generate_langgraph_project_creates_structure(tmp_path: Path) -> None:
    ir = _make_branching_ir()

    project = generate_langgraph_project(ir, destination=tmp_path / "app")

    assert isinstance(project, LangGraphProject)
    src_root = project.root / "src" / project.package_name
    tests_root = project.root / "tests" / "smoke"

    graph_module = src_root / "graphs" / "main_graph.py"
    init_file = src_root / "__init__.py"
    nodes_init = src_root / "nodes" / "__init__.py"
    state_module = src_root / "state.py"
    prompts_init = src_root / "prompts" / "__init__.py"
    tools_dir = src_root / "tools"
    config_dir = src_root / "config"
    cli_module = src_root / "cli.py"
    smoke_test = tests_root / "test_flow.py"
    pyproject = project.root / "pyproject.toml"

    assert graph_module.exists()
    assert init_file.exists()
    assert nodes_init.exists()
    assert state_module.exists()
    assert prompts_init.exists()
    assert (tools_dir / "__init__.py").exists()
    assert (tools_dir / "base_tool.py").exists()
    assert (config_dir / "__init__.py").exists()
    assert (config_dir / "settings.py").exists()
    assert cli_module.exists()
    assert smoke_test.exists()
    assert pyproject.exists()

    graph_content = graph_module.read_text()
    assert ir.flow_id in graph_content
    assert "StateGraph" in graph_content

    smoke_content = smoke_test.read_text()
    assert "main_graph" in smoke_content
    assert "langgraph" in pyproject.read_text().lower()

    statuses = {entry.status for entry in project.writes}
    assert "created" in statuses
    assert len(project.writes) >= 8

    generate_langgraph_project(ir, destination=project.root)


def test_generate_langgraph_project_rejects_linear_flows(tmp_path: Path) -> None:
    ir = _make_linear_ir()

    with pytest.raises(ValueError, match="LangChain"):
        generate_langgraph_project(ir, destination=tmp_path / "app")
