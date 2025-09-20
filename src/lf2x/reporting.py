"""Conversion reporting utilities for LF2X."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .analyzer import TargetRecommendation
from .generators.project import WriteResult, WriteStatus


@dataclass(frozen=True, slots=True)
class ReportEntry:
    """Single file entry within a conversion report."""

    path: Path
    status: WriteStatus
    todos: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConversionReport:
    """Structured summary of a flow conversion."""

    flow_id: str
    target: TargetRecommendation
    project_root: Path
    entries: tuple[ReportEntry, ...]

    @property
    def counts(self) -> Counter[str]:
        """Return a counter of entry statuses."""

        return Counter(entry.status for entry in self.entries)


@dataclass(frozen=True, slots=True)
class ReportArtifacts:
    """Paths to persisted conversion report artifacts."""

    markdown: Path
    json: Path


def build_report(
    *,
    flow_id: str,
    target: TargetRecommendation,
    project_root: Path,
    writes: Iterable[WriteResult],
) -> ConversionReport:
    """Build a conversion report structure from generation metadata."""

    entries: list[ReportEntry] = []
    root = project_root.resolve()
    for write in writes:
        path = write.path
        try:
            relative = path.resolve().relative_to(root)
        except ValueError:
            relative = path
        entries.append(ReportEntry(path=relative, status=write.status, todos=write.todos))
    return ConversionReport(
        flow_id=flow_id,
        target=target,
        project_root=root,
        entries=tuple(entries),
    )


def write_conversion_report(
    *,
    flow_id: str,
    target: TargetRecommendation,
    project_root: Path,
    writes: Iterable[WriteResult],
    destination: Path | None = None,
) -> ReportArtifacts:
    """Write conversion reports to disk and return their locations."""

    report = build_report(
        flow_id=flow_id,
        target=target,
        project_root=project_root,
        writes=writes,
    )
    output_dir = (destination or project_root).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = output_dir / "conversion_report.md"
    json_path = output_dir / "conversion_report.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(_render_json(report), encoding="utf-8")
    return ReportArtifacts(markdown=markdown_path, json=json_path)


def _render_markdown(report: ConversionReport) -> str:
    counts = report.counts
    lines: list[str] = [
        f"# Conversion Report for `{report.flow_id}`",
        "",
        f"- Target: {report.target.value}",
        f"- Project root: `{report.project_root}`",
        f"- Files created: {counts.get('created', 0)}",
        f"- Files updated: {counts.get('updated', 0)}",
        f"- Files unchanged: {counts.get('unchanged', 0)}",
        "",
        "## Files",
        "| Path | Status | TODOs |",
        "| --- | --- | --- |",
    ]
    for entry in report.entries:
        todos = "<br />".join(entry.todos) if entry.todos else ""
        lines.append(f"| {entry.path} | {entry.status} | {todos} |")
    return "\n".join(lines) + "\n"


def _render_json(report: ConversionReport) -> str:
    payload = {
        "flow_id": report.flow_id,
        "target": report.target.value,
        "project_root": str(report.project_root),
        "counts": dict(report.counts),
        "files": [
            {
                "path": str(entry.path),
                "status": entry.status,
                "todos": list(entry.todos),
            }
            for entry in report.entries
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


__all__ = [
    "ConversionReport",
    "ReportArtifacts",
    "ReportEntry",
    "build_report",
    "write_conversion_report",
]
