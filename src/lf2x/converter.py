"""Conversion orchestration pipeline for LF2X."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analyzer import TargetRecommendation, analyze_flow
from .config import LF2XSettings
from .generators.langchain import generate_langchain_project
from .generators.langgraph import generate_langgraph_project
from .generators.project import WriteResult
from .ir import IntermediateRepresentation, build_intermediate_representation
from .naming import slugify
from .parser import LangFlowDocument, parse_langflow_json


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Summary of a single flow conversion."""

    flow_id: str
    target: TargetRecommendation
    project_root: Path
    package_name: str
    writes: tuple[WriteResult, ...]


def convert_flow(
    source: Path | str,
    *,
    settings: LF2XSettings | None = None,
    overwrite: bool = False,
) -> ConversionResult:
    """High-level helper that parses, analyzes, and generates a project."""

    active_settings = settings or LF2XSettings()
    document = parse_langflow_json(source, settings=active_settings)
    return convert_document(document, overwrite=overwrite)


def convert_document(
    document: LangFlowDocument,
    *,
    overwrite: bool = False,
) -> ConversionResult:
    """Convert a parsed LangFlow document into a generated project."""

    ir = build_intermediate_representation(document)
    return _generate_project(ir, overwrite=overwrite)


def _generate_project(ir: IntermediateRepresentation, *, overwrite: bool) -> ConversionResult:
    analysis = analyze_flow(ir)

    if analysis.recommended_target is TargetRecommendation.LANGCHAIN:
        destination = _destination_root(ir, default="lf2x_project")
        chain_project = generate_langchain_project(ir, destination=destination, overwrite=overwrite)
        return ConversionResult(
            flow_id=ir.flow_id,
            target=TargetRecommendation.LANGCHAIN,
            project_root=chain_project.root,
            package_name=chain_project.package_name,
            writes=chain_project.writes,
        )

    destination = _destination_root(ir, default="lf2x_graph")
    graph_project = generate_langgraph_project(ir, destination=destination, overwrite=overwrite)
    return ConversionResult(
        flow_id=ir.flow_id,
        target=TargetRecommendation.LANGGRAPH,
        project_root=graph_project.root,
        package_name=graph_project.package_name,
        writes=graph_project.writes,
    )


def _destination_root(ir: IntermediateRepresentation, *, default: str) -> Path:
    base = ir.metadata.output_dir
    slug = slugify(ir.flow_id, default=default)
    return base / slug


__all__ = ["ConversionResult", "convert_document", "convert_flow"]
