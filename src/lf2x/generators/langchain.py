"""Generate LangChain/LCEL projects from Intermediate Representations."""

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

SUPPORTED_PATTERN = FlowPattern.LINEAR


@dataclass(frozen=True, slots=True)
class LangChainProject:
    """Metadata about a generated LangChain project."""

    root: Path
    package_name: str
    flow_id: str
    writes: tuple[WriteResult, ...]


def generate_langchain_project(
    ir: IntermediateRepresentation,
    *,
    destination: Path,
    overwrite: bool = False,
) -> LangChainProject:
    """Generate a minimal LangChain/LCEL project for a linear flow."""

    analysis = analyze_flow(ir)
    if analysis.pattern is not SUPPORTED_PATTERN:
        raise ValueError(
            "LangChain generator only supports linear flows. "
            "Use the LangGraph generator for branching/cyclic flows."
        )

    root = destination.resolve()
    package_name = slugify(ir.flow_id, default="lf2x_project")
    writer = ProjectScaffoldWriter(root, overwrite=overwrite)
    secrets = detect_secrets(ir)
    writes = writer.write_files(_build_files(package_name, ir, secrets))

    return LangChainProject(
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
        "__all__ = ['build_chain', 'run_chain']\n",
    )
    yield GeneratedFile(
        Path("src") / package_name / "chains" / "__init__.py",
        "from .main_chain import build_chain, run_chain\n",
    )
    yield GeneratedFile(
        Path("src") / package_name / "chains" / "main_chain.py",
        _render_main_chain(ir),
    )
    yield GeneratedFile(
        Path("src") / package_name / "nodes" / "__init__.py",
        _render_nodes_init(),
        todos=("Populate node factories for the generated flow",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "prompts" / "__init__.py",
        _render_prompts_init(),
        todos=("Replace prompt registry with project-specific prompts",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "prompts" / "system_prompt.txt",
        _render_prompt_stub(ir),
        todos=("Author the system prompt for this flow",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "tools" / "__init__.py",
        _render_tools_init(),
        todos=("Wire LangFlow tools into executable adapters",),
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
        todos=("Map generated components to real configuration values",),
    )
    yield GeneratedFile(
        Path("src") / package_name / "cli.py",
        _render_cli_module(package_name),
        todos=("Extend CLI commands to match production needs",),
    )
    yield GeneratedFile(
        Path("tests") / "smoke" / "test_flow.py",
        _render_smoke_test(package_name, ir),
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
        todos=("Set real secret values for deployment",),
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
            description = "Auto-generated LangChain project"
            requires-python = ">=3.11"
            dependencies = ["langchain>=0.1"]
            """
        )
        .strip()
        .format(project_name=package_name.replace("_", "-"))
        + "\n"
    )


def _render_main_chain(ir: IntermediateRepresentation) -> str:
    nodes_literal = ",\n        ".join(repr(node.node_id) for node in ir.nodes)
    template = textwrap.dedent('''
        """LangChain chain stub generated from flow {flow_id}."""

        from typing import Any, List

        NODES: List[str] = [
            {nodes}
        ]


        def build_chain() -> List[str]:
            """Return the ordered list of node identifiers for this flow."""

            return NODES.copy()


        def run_chain(message: str, *, debug: bool = False) -> dict[str, Any]:
            """Placeholder execution stub for the generated chain."""

            if debug:
                print("Running chain with message:", message)
            return {{"message": message}}
        ''')
    return template.strip().format(flow_id=ir.flow_id, nodes=nodes_literal) + "\n"


def _render_nodes_init() -> str:
    return (
        textwrap.dedent(
            '''
        """Node placeholders for the generated flow."""

        __all__: list[str] = []
        '''
        ).strip()
        + "\n"
    )


def _render_prompts_init() -> str:
    return (
        textwrap.dedent(
            '''
        """Prompt registry for the generated chain."""

        from pathlib import Path

        PROMPT_DIR = Path(__file__).parent


        def load_system_prompt() -> str:
            """Return the system prompt placeholder."""

            return (PROMPT_DIR / "system_prompt.txt").read_text(encoding="utf-8")
        '''
        ).strip()
        + "\n"
    )


def _render_prompt_stub(ir: IntermediateRepresentation) -> str:
    name = ir.name or ir.flow_id
    return (
        textwrap.dedent(
            f"""
        You are the orchestrator for the LangFlow-derived project "{name}".
        Tailor this prompt to steer the chain behaviour.
        """
        ).strip()
        + "\n"
    )


def _render_tools_init() -> str:
    return (
        textwrap.dedent(
            '''
        """Tool adapters for connecting LangFlow tools to LangChain."""

        from typing import Any


        def list_tools() -> list[str]:
            """Return the available tool identifiers."""

            return []


        def resolve_tool(name: str) -> Any:
            """Resolve a tool by name."""

            raise KeyError(name)
        '''
        ).strip()
        + "\n"
    )


def _render_tool_stub() -> str:
    return (
        textwrap.dedent(
            '''
        """Base class for custom LangChain tool implementations."""

        from abc import ABC, abstractmethod
        from typing import Any


        class GeneratedTool(ABC):
            """Extend this class to wrap LangFlow tool nodes."""

            name: str = "lf2x_tool"

            @abstractmethod
            def run(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - interface
                """Execute the tool."""

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
        """Runtime settings for the generated LangChain project."""

        from __future__ import annotations

        import os
        from dataclasses import dataclass


        @dataclass(slots=True)
        class Settings:
            """Container for environment-driven configuration."""

{field_lines}


        def load_settings() -> Settings:
            """Load configuration from environment variables."""

            return Settings(
{assignment_lines}
            )


        settings = load_settings()
        '''
        return textwrap.dedent(template).strip() + "\n"

    return (
        textwrap.dedent(
            '''
        """Runtime settings for the generated LangChain project."""

        from __future__ import annotations

        import os
        from dataclasses import dataclass


        @dataclass(slots=True)
        class Settings:
            """Container for environment-driven configuration."""

            example_api_key: str | None


        def load_settings() -> Settings:
            """Load configuration from environment variables."""

            return Settings(example_api_key=os.getenv("EXAMPLE_API_KEY"))


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
        """Command line helpers for the {package_name} package."""

        from typing import Any

        from .chains.main_chain import run_chain


        def main(message: str = "Hello from LF2X") -> dict[str, Any]:
            """Run the generated chain with a sample payload."""

            return run_chain(message, debug=True)


        if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
            response = main()
            print(response)
        '''
        ).strip()
        + "\n"
    )


def _render_smoke_test(package_name: str, ir: IntermediateRepresentation) -> str:
    content = (
        textwrap.dedent(
            """
        from {pkg}.chains.main_chain import build_chain, run_chain


        def test_build_chain_returns_nodes() -> None:
            chain = build_chain()
            assert chain
            assert {first_node!r} in chain


        def test_run_chain_returns_payload() -> None:
            result = run_chain("hello")
            assert result["message"] == "hello"
        """
        )
        .strip()
        .format(pkg=package_name, first_node=ir.nodes[0].node_id if ir.nodes else "")
    )
    return content + "\n"


def _render_unit_test_config(package_name: str, secrets: tuple[DetectedSecret, ...]) -> str:
    fields_assertion = "\n    ".join(
        f"assert hasattr(settings, '{secret.attribute}')" for secret in secrets
    )
    body = textwrap.dedent(
        f"""
        from {package_name}.config import settings


        def test_settings_exposes_expected_attributes() -> None:
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


        def test_cli_main_returns_payload() -> None:
            result = main("ping")
            assert result["message"] == "ping"
        """
        ).strip()
        + "\n"
    )


def _render_readme(ir: IntermediateRepresentation) -> str:
    content = (
        textwrap.dedent(
            """
        # {name}

        Auto-generated LangChain project for flow `{flow_id}`.

        ## Structure
        - `chains/`: LCEL orchestration logic
        - `nodes/`: place custom node adapters here
        - `prompts/`: text assets powering the chain
        - `tools/`: wrappers for external integrations
        - `config/`: environment-driven settings
        - `cli.py`: convenience entrypoint for local execution
        - `.env.example`: template for environment secrets
        """
        )
        .strip()
        .format(name=ir.name or ir.flow_id, flow_id=ir.flow_id)
    )
    return content + "\n"


__all__ = ["LangChainProject", "generate_langchain_project"]
