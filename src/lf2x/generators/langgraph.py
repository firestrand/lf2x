"""Generate LangGraph projects from Intermediate Representations."""

from __future__ import annotations

import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ..analyzer import FlowPattern, analyze_flow
from ..extractors import DetectedSecret, detect_secrets
from ..ir import IntermediateRepresentation
from ..naming import slugify
from .project import GeneratedFile, ProjectScaffoldWriter, WriteResult

SUPPORTED_PATTERNS = {FlowPattern.BRANCHING, FlowPattern.CYCLIC}


@dataclass(frozen=True, slots=True)
class LangGraphProject:
    root: Path
    package_name: str
    flow_id: str
    writes: tuple[WriteResult, ...]


def generate_langgraph_project(
    ir: IntermediateRepresentation,
    *,
    destination: Path,
    overwrite: bool = False,
) -> LangGraphProject:
    analysis = analyze_flow(ir)
    if analysis.pattern not in SUPPORTED_PATTERNS:
        raise ValueError(
            "LangGraph generator expects branching or cyclic flows. "
            "Use the LangChain generator for linear flows."
        )

    root = destination.resolve()
    package_name = slugify(ir.name or ir.flow_id, default="lf2x_graph")
    writer = ProjectScaffoldWriter(root, overwrite=overwrite)
    secrets = detect_secrets(ir)
    writes = writer.write_files(_build_files(package_name, ir, secrets))

    return LangGraphProject(
        root=root,
        package_name=package_name,
        flow_id=ir.flow_id,
        writes=tuple(writes),
    )


def _build_files(
    package_name: str,
    ir: IntermediateRepresentation,
    secrets: Iterable[DetectedSecret],
) -> Iterable[GeneratedFile]:
    detected = tuple(secrets)
    yield GeneratedFile(Path("pyproject.toml"), _render_pyproject(package_name))
    yield GeneratedFile(
        Path("src") / package_name / "__init__.py",
        "__all__ = ['build_graph', 'iter_edges']\n",
    )
    yield GeneratedFile(
        Path("src") / package_name / "graphs" / "__init__.py",
        "from .main_graph import build_graph, iter_edges\n",
    )
    yield GeneratedFile(
        Path("src") / package_name / "graphs" / "main_graph.py",
        _render_main_graph(ir),
    )
    yield GeneratedFile(
        Path("src") / package_name / "nodes" / "__init__.py",
        _render_nodes_init(),
        todos=("Implement node-level handlers for LangGraph",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "state.py",
        _render_state_module(),
        todos=("Define structured state for graph execution",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "prompts" / "__init__.py",
        _render_prompts_init(),
        todos=("Customize prompt formatting for the generated flow",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "tools" / "__init__.py",
        _render_tools_init(),
        todos=("Hook external tools into the graph",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "tools" / "base_tool.py",
        _render_tool_stub(),
    )
    yield GeneratedFile(
        Path("src") / package_name / "config" / "__init__.py",
        _render_config_init(),
    )
    yield GeneratedFile(
        Path("src") / package_name / "config" / "settings.py",
        _render_config_settings(detected),
        todos=("Connect graph configuration to deployment runtime",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "cli.py",
        _render_cli_module(package_name),
        todos=("Expose graph operations via CLI",),
    )
    yield GeneratedFile(
        Path("tests") / "smoke" / "test_flow.py",
        _render_smoke_test(package_name),
    )
    yield GeneratedFile(
        Path("tests") / "unit" / "test_config.py",
        _render_unit_test_config(package_name, detected),
    )
    yield GeneratedFile(
        Path("tests") / "unit" / "test_cli.py",
        _render_unit_test_cli(package_name),
    )
    yield GeneratedFile(Path("README.md"), _render_readme(ir))
    yield GeneratedFile(
        Path(".env.example"),
        _render_env_example(detected),
        todos=("Set graph secrets before deployment",),
    )


def _render_pyproject(package_name: str) -> str:
    return (
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=68"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "{project_name}"
            version = "0.0.0"
            description = "Auto-generated LangGraph project"
            requires-python = ">=3.11"
            dependencies = ["langgraph>=0.0.30"]
            """
        )
        .strip()
        .format(project_name=package_name.replace("_", "-"))
        + "\n"
    )


def _render_main_graph(ir: IntermediateRepresentation) -> str:
    nodes_literal = ",\n    ".join(repr(node.node_id) for node in ir.nodes)
    edges_literal = ",\n    ".join(f"({edge.source!r}, {edge.target!r})" for edge in ir.edges)
    template = (
        textwrap.dedent(
            '''
        """LangGraph state graph stub generated from flow {flow_id}."""

        from collections.abc import Iterator
        from typing import Any

        from langgraph.graph import END, Graph, StateGraph

        NODE_IDS = [
            {nodes}
        ]
        EDGE_IDS: list[tuple[str, str]] = [
            {edges}
        ]


        def build_graph(debug: bool = False) -> Graph:
            graph = StateGraph(dict[str, Any])
            for node in NODE_IDS:
                graph.add_node(node, lambda state: state)
            for source, target in EDGE_IDS:
                graph.add_edge(source, target)
            if EDGE_IDS:
                graph.add_edge(EDGE_IDS[-1][1], END)
            if debug:
                print("Building graph for flow {flow_id} with nodes:", NODE_IDS)
            return graph.compile()


        def iter_edges() -> Iterator[tuple[str, str]]:
            yield from EDGE_IDS
        '''
        )
        .strip()
        .format(flow_id=ir.flow_id, nodes=nodes_literal, edges=edges_literal)
    )
    return template + "\n"


def _render_nodes_init() -> str:
    return (
        textwrap.dedent(
            '''
        """Hook points for LangGraph node behaviours."""

        __all__: list[str] = []
        '''
        ).strip()
        + "\n"
    )


def _render_state_module() -> str:
    return (
        textwrap.dedent(
            '''
        """State definition for the generated LangGraph project."""

        from __future__ import annotations

        from dataclasses import dataclass, field
        from typing import Any


        @dataclass(slots=True)
        class GraphState:
            """Mutable state shared across LangGraph nodes."""

            data: dict[str, Any] = field(default_factory=dict)


        def new_state() -> GraphState:
            """Return a fresh graph state."""

            return GraphState()
        '''
        ).strip()
        + "\n"
    )


def _render_prompts_init() -> str:
    return (
        textwrap.dedent(
            '''
        """Prompt utilities for the generated LangGraph."""

        def format_system_prompt(flow_name: str) -> str:
            """Return a placeholder system prompt for the graph."""

            return f"System prompt for {flow_name}. Replace with flow-specific instructions."
        '''
        ).strip()
        + "\n"
    )


def _render_tools_init() -> str:
    return (
        textwrap.dedent(
            '''
        """Tool registry for graph execution."""

        from typing import Any


        def list_tools() -> list[str]:
            """Return identifiers for available graph tools."""

            return []


        def resolve_tool(name: str) -> Any:
            """Resolve a graph tool by name."""

            raise KeyError(name)
        '''
        ).strip()
        + "\n"
    )


def _render_tool_stub() -> str:
    return (
        textwrap.dedent(
            '''
        """Base class for LangGraph tool integrations."""

        from __future__ import annotations

        from abc import ABC, abstractmethod
        from typing import Any


        class GraphTool(ABC):
            """Subclass to expose LangFlow tools within the state graph."""

            name: str = "lf2x_graph_tool"

            @abstractmethod
            def invoke(self, state: Any) -> Any:  # pragma: no cover - interface
                """Execute the tool against the provided state."""

                raise NotImplementedError
        '''
        ).strip()
        + "\n"
    )


def _render_config_init() -> str:
    return "from .settings import settings\n"


def _render_config_settings(secrets: tuple[DetectedSecret, ...]) -> str:
    if secrets:
        field_lines = "\n".join(f"            {secret.attribute}: str | None" for secret in secrets)
        assignment_lines = "\n".join(
            f"                {secret.attribute}=os.getenv('{secret.env_var}'),"
            for secret in secrets
        )
        template = f'''
        """Configuration helpers for the generated LangGraph project."""

        from __future__ import annotations

        import os
        from dataclasses import dataclass


        @dataclass(slots=True)
        class Settings:
            """Define environment-derived configuration knobs."""

{field_lines}


        def load_settings() -> Settings:
            """Load settings from the environment."""

            return Settings(
{assignment_lines}
            )


        settings = load_settings()
        '''
        return textwrap.dedent(template).strip() + "\n"

    return (
        textwrap.dedent(
            '''
        """Configuration helpers for the generated LangGraph project."""

        from __future__ import annotations

        import os
        from dataclasses import dataclass


        @dataclass(slots=True)
        class Settings:
            """Define environment-derived configuration knobs."""

            tracing_enabled: bool


        def load_settings() -> Settings:
            """Load settings from the environment."""

            value = os.getenv("LF2X_ENABLE_TRACING", "false").lower()
            return Settings(tracing_enabled=value in {"1", "true", "yes"})


        settings = load_settings()
        '''
        ).strip()
        + "\n"
    )


def _render_env_example(secrets: tuple[DetectedSecret, ...]) -> str:
    if not secrets:
        return "# No secrets detected in the flow. Add environment variables as needed.\n"

    lines: list[str] = ["# Populate these secrets before deploying."]
    for secret in secrets:
        lines.append(f"# Source: node {secret.source_node}, field {secret.field}")
        lines.append(f"{secret.env_var}=")
    return "\n".join(lines) + "\n"


def _render_cli_module(package_name: str) -> str:
    return (
        textwrap.dedent(
            f'''
        """Command line helpers for the {package_name} LangGraph project."""

        from typing import Any

        from .graphs.main_graph import build_graph
        from .state import new_state


        def main(debug: bool = True) -> Any:
            """Compile the graph and run it with a blank state."""

            graph = build_graph(debug=debug)
            return graph.invoke(new_state()) if hasattr(graph, "invoke") else graph


        if __name__ == "__main__":  # pragma: no cover - helper entrypoint
            result = main()
            print(result)
        '''
        ).strip()
        + "\n"
    )


def _render_smoke_test(package_name: str) -> str:
    content = textwrap.dedent(
        f"""
        from {package_name}.graphs.main_graph import build_graph, iter_edges


        def test_build_graph_returns_nodes_and_edges() -> None:
            graph = build_graph()
            assert graph


        def test_iter_edges_yields_edges() -> None:
            edges = list(iter_edges())
            assert edges
        """
    ).strip()
    return content + "\n"


def _render_unit_test_config(package_name: str, secrets: tuple[DetectedSecret, ...]) -> str:
    fields_assertion = "\n    ".join(
        f"assert hasattr(settings, '{secret.attribute}')" for secret in secrets
    )
    body = textwrap.dedent(
        f"""
        from {package_name}.config import settings


        def test_settings_flags_are_accessible() -> None:
            assert settings is not None
        """
    ).strip()
    if fields_assertion:
        body += f"\n    {fields_assertion}"
    return body + "\n"


def _render_unit_test_cli(package_name: str) -> str:
    return (
        textwrap.dedent(
            f"""
        from {package_name}.cli import main


        def test_cli_main_builds_graph() -> None:
            graph = main(debug=False)
            assert graph is not None
        """
        ).strip()
        + "\n"
    )


def _render_readme(ir: IntermediateRepresentation) -> str:
    content = textwrap.dedent(
        f"""
        # {ir.name or ir.flow_id}

        Auto-generated LangGraph project for flow `{ir.flow_id}`.

        ## Structure
        - `graphs/`: state graph construction logic
        - `nodes/`: adapters for individual LangFlow nodes
        - `state.py`: shared state definitions
        - `prompts/`: messaging helpers
        - `tools/`: interfaces to external tools
        - `config/`: runtime configuration helpers
        - `cli.py`: basic command line runner
        - `.env.example`: template for environment secrets
        """
    ).strip()
    return content + "\n"


__all__ = ["LangGraphProject", "generate_langgraph_project"]
