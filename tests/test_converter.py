from __future__ import annotations

from pathlib import Path

import pytest

from lf2x.analyzer import TargetRecommendation
from lf2x.config import LF2XSettings
from lf2x.converter import ConversionResult, convert_flow
from lf2x.generators.project import OverwriteError

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "flows"


@pytest.mark.parametrize(  # type: ignore[misc]
    ("fixture", "expected_target"),
    [
        ("simple_passthrough.json", TargetRecommendation.LANGCHAIN),
        ("price_deal_finder.json", TargetRecommendation.LANGGRAPH),
    ],
)
def test_convert_flow_selects_target(
    tmp_path: Path, fixture: str, expected_target: TargetRecommendation
) -> None:
    output_dir = tmp_path / "artifacts"
    settings = LF2XSettings(output_dir=output_dir)

    result = convert_flow(FIXTURE_DIR / fixture, settings=settings)

    assert isinstance(result, ConversionResult)
    assert result.target is expected_target
    assert result.project_root.exists()
    assert result.project_root.is_dir()
    assert output_dir in result.project_root.parents or result.project_root == output_dir
    assert (result.project_root / "pyproject.toml").exists()
    assert result.writes
    assert any(entry.status == "created" for entry in result.writes)


def test_convert_flow_requires_overwrite_when_files_diverge(tmp_path: Path) -> None:
    output_dir = tmp_path / "projects"
    settings = LF2XSettings(output_dir=output_dir)
    source = FIXTURE_DIR / "simple_passthrough.json"

    result = convert_flow(source, settings=settings)
    project_root = result.project_root
    main_chain = project_root / "src" / result.package_name / "chains" / "main_chain.py"
    main_chain.write_text("mutated\n")

    with pytest.raises(OverwriteError):
        convert_flow(source, settings=settings)

    overwrite_result = convert_flow(source, settings=settings, overwrite=True)
    assert any(entry.status in {"updated", "would-update"} for entry in overwrite_result.writes)
