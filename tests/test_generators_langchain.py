from __future__ import annotations

from pathlib import Path

import pytest

from lf2x.generators.langchain import LangChainProject, generate_langchain_project
from lf2x.ir import (
    IntermediateRepresentation,
    IRMetadata,
    IRNode,
    build_intermediate_representation,
)
from lf2x.parser import parse_langflow_json

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "flows"


def _build_ir(fixture_name: str) -> IntermediateRepresentation:
    document = parse_langflow_json(FIXTURE_DIR / fixture_name)
    return build_intermediate_representation(document)


def test_generate_langchain_project_creates_expected_structure(tmp_path: Path) -> None:
    ir = _build_ir("simple_passthrough.json")

    project = generate_langchain_project(ir, destination=tmp_path / "app")

    assert isinstance(project, LangChainProject)
    src_root = project.root / "src" / project.package_name
    tests_root = project.root / "tests" / "smoke"

    main_chain = src_root / "chains" / "main_chain.py"
    init_file = src_root / "__init__.py"
    nodes_init = src_root / "nodes" / "__init__.py"
    prompts_dir = src_root / "prompts"
    tools_dir = src_root / "tools"
    config_dir = src_root / "config"
    cli_module = src_root / "cli.py"
    smoke_test = tests_root / "test_flow.py"
    unit_config_test = project.root / "tests" / "unit" / "test_config.py"
    unit_cli_test = project.root / "tests" / "unit" / "test_cli.py"
    pyproject = project.root / "pyproject.toml"
    env_file = project.root / ".env.example"

    assert main_chain.exists()
    assert init_file.exists()
    assert nodes_init.exists()
    assert (prompts_dir / "__init__.py").exists()
    assert (prompts_dir / "system_prompt.txt").exists()
    assert (tools_dir / "__init__.py").exists()
    assert (tools_dir / "base_tool.py").exists()
    assert (config_dir / "__init__.py").exists()
    assert (config_dir / "settings.py").exists()
    assert cli_module.exists()
    assert smoke_test.exists()
    assert unit_config_test.exists()
    assert unit_cli_test.exists()
    assert pyproject.exists()

    main_chain_content = main_chain.read_text()
    assert ir.flow_id in main_chain_content
    assert "LangChain" in main_chain_content

    smoke_content = smoke_test.read_text()
    assert "main_chain" in smoke_content
    assert "langchain" in pyproject.read_text().lower()
    system_prompt = (prompts_dir / "system_prompt.txt").read_text()
    assert ir.name or ir.flow_id in system_prompt
    assert env_file.exists()
    assert "No secrets detected" in env_file.read_text()

    statuses = {entry.status for entry in project.writes}
    assert "created" in statuses
    assert len(project.writes) >= 8

    # Running again should be idempotent
    generate_langchain_project(ir, destination=project.root)


def test_generate_langchain_project_extracts_secrets(tmp_path: Path) -> None:
    secret_ir = IntermediateRepresentation(
        flow_id="SecretFlow",
        name="Secret Flow",
        version="1.0.0",
        nodes=(IRNode("provider", "SecretNode", {"api_key": "sk-test"}),),
        edges=(),
        metadata=IRMetadata(Path("secret.json"), Path("dist")),
    )

    project = generate_langchain_project(secret_ir, destination=tmp_path / "app")

    env_file = project.root / ".env.example"
    settings_file = project.root / "src" / project.package_name / "config" / "settings.py"

    assert "SECRETFLOW_PROVIDER_API_KEY" in env_file.read_text()
    settings_content = settings_file.read_text()
    assert "secretflow_provider_api_key" in settings_content


def test_generate_langchain_project_rejects_branching_flows(tmp_path: Path) -> None:
    branching_ir = _build_ir("price_deal_finder.json")

    with pytest.raises(ValueError, match="LangGraph"):
        generate_langchain_project(branching_ir, destination=tmp_path / "app")
