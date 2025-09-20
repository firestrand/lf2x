from __future__ import annotations

from pathlib import Path

import pytest

from lf2x.generators.project import (
    GeneratedFile,
    OverwriteError,
    ProjectScaffoldWriter,
    WriteResult,
)


def test_writer_creates_files(tmp_path: Path) -> None:
    writer = ProjectScaffoldWriter(tmp_path)
    files = [
        GeneratedFile(Path("README.md"), "# Demo\n"),
        GeneratedFile(Path("src") / "app.py", "print('hi')\n"),
    ]

    written = writer.write_files(files)

    assert len(written) == 2
    assert {result.status for result in written} == {"created"}
    assert all(result.todos == () for result in written)
    assert (tmp_path / "README.md").read_text() == "# Demo\n"
    assert (tmp_path / "src" / "app.py").read_text() == "print('hi')\n"


def test_writer_is_idempotent(tmp_path: Path) -> None:
    writer = ProjectScaffoldWriter(tmp_path)
    file = GeneratedFile(Path("config.toml"), "[tool]\nname='demo'\n")

    first = writer.write_files([file])
    assert first == [WriteResult(path=tmp_path / "config.toml", status="created", todos=())]

    second = writer.write_files([file])
    assert second == [WriteResult(path=tmp_path / "config.toml", status="unchanged", todos=())]


def test_writer_rejects_conflicting_file(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("original\n")
    writer = ProjectScaffoldWriter(tmp_path)

    with pytest.raises(OverwriteError):
        writer.write_files([GeneratedFile(Path("README.md"), "changed\n")])


def test_writer_overwrites_when_enabled(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("original\n")
    writer = ProjectScaffoldWriter(tmp_path, overwrite=True)

    result = writer.write_files([GeneratedFile(Path("README.md"), "changed\n")])

    assert result == [WriteResult(path=target, status="updated", todos=())]
    assert target.read_text() == "changed\n"


def test_writer_injects_todo_comments(tmp_path: Path) -> None:
    writer = ProjectScaffoldWriter(tmp_path)
    file = GeneratedFile(Path("src") / "module.py", "print('hi')\n", todos=("review logic",))

    results = writer.write_files([file])

    assert results == [
        WriteResult(
            path=tmp_path / "src" / "module.py",
            status="created",
            todos=("review logic",),
        )
    ]
    content = (tmp_path / "src" / "module.py").read_text()
    assert content.startswith("# TODO(lf2x): review logic\n\n")
    assert "print('hi')" in content


def test_writer_rejects_todo_for_unknown_suffix(tmp_path: Path) -> None:
    writer = ProjectScaffoldWriter(tmp_path)
    file = GeneratedFile(Path("binary.bin"), "data", todos=("cannot annotate",))

    with pytest.raises(ValueError, match="Cannot inject TODO"):
        writer.write_files([file])


def test_writer_dry_run(tmp_path: Path) -> None:
    writer = ProjectScaffoldWriter(tmp_path, dry_run=True)
    file = GeneratedFile(Path("README.md"), "# Demo\n")

    results = writer.write_files([file])

    assert results == [WriteResult(path=tmp_path / "README.md", status="would-create", todos=())]
    assert not (tmp_path / "README.md").exists()
