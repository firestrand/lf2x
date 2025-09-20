"""Project scaffold writer utilities for LF2X generators."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast


class OverwriteError(RuntimeError):
    """Raised when attempting to overwrite an existing file without permission."""


_COMMENT_PREFIXES: dict[str, str] = {
    ".py": "#",
    ".toml": "#",
    ".md": ">",
    ".txt": "#",
    ".yaml": "#",
    ".yml": "#",
    ".ini": "#",
    ".cfg": "#",
    ".env": "#",
    ".example": "#",
}


@dataclass(slots=True)
class GeneratedFile:
    """Descriptor for a file the generators should materialize."""

    relative_path: Path
    content: str
    todos: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - trivial normalization
        if not isinstance(self.relative_path, Path):
            self.relative_path = Path(self.relative_path)
        if self.relative_path.is_absolute():
            raise ValueError("Generated files must use relative paths")
        if not isinstance(self.todos, tuple):
            self.todos = tuple(self.todos)


WriteStatus = Literal["created", "updated", "unchanged", "would-create", "would-update"]


@dataclass(frozen=True, slots=True)
class WriteResult:
    """Result of attempting to persist a generated file."""

    path: Path
    status: WriteStatus
    todos: tuple[str, ...] = ()


class ProjectScaffoldWriter:
    """Write generated project files with idempotent semantics."""

    def __init__(
        self,
        root: Path,
        *,
        overwrite: bool = False,
        encoding: str = "utf-8",
        dry_run: bool = False,
    ) -> None:
        self.root = root.resolve()
        self.overwrite = overwrite
        self.encoding = encoding
        self.dry_run = dry_run

    def write_files(self, files: Iterable[GeneratedFile]) -> list[WriteResult]:
        """Write the provided files to disk and return the touched paths."""

        written: list[WriteResult] = []
        for file in files:
            target = self.root / file.relative_path
            if not self.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
            content = self._render_content(target, file)
            if target.exists():
                existing = target.read_text(encoding=self.encoding)
                if existing == content:
                    written.append(
                        WriteResult(path=target, status="unchanged", todos=tuple(file.todos))
                    )
                    continue
                if not self.overwrite:
                    raise OverwriteError(
                        f"Refusing to overwrite existing file without --overwrite: {target}"
                    )
                status = cast(WriteStatus, "would-update" if self.dry_run else "updated")
                if not self.dry_run:
                    target.write_text(content, encoding=self.encoding)
                written.append(WriteResult(path=target, status=status, todos=tuple(file.todos)))
                continue

            status = cast(WriteStatus, "would-create" if self.dry_run else "created")
            if not self.dry_run:
                target.write_text(content, encoding=self.encoding)
            written.append(WriteResult(path=target, status=status, todos=tuple(file.todos)))
        return written

    def _render_content(self, target: Path, file: GeneratedFile) -> str:
        body = file.content if file.content.endswith("\n") else f"{file.content}\n"
        if not file.todos:
            return body
        prefix = _COMMENT_PREFIXES.get(target.suffix)
        if prefix is None:
            raise ValueError(
                f"Cannot inject TODO markers for unsupported file type: {target.suffix or '<none>'}"
            )
        todo_block = "\n".join(f"{prefix} TODO(lf2x): {item}" for item in file.todos)
        return f"{todo_block}\n\n{body}"


__all__ = [
    "GeneratedFile",
    "OverwriteError",
    "ProjectScaffoldWriter",
    "WriteResult",
    "WriteStatus",
]
