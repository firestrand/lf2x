# LF2X

LangFlow to X (LF2X) converts LangFlow visual workflows into production-grade LangGraph and LangChain projects. The repository houses the conversion engine, CLI tooling, and supporting documentation.

## Key Principles
- Default to a modular `src/lf2x` codebase with generated artifacts written outside the repository (e.g., `dist/`).
- Enforce code quality via `ruff`, `mypy`, `vulture`, and a TDD workflow with ≥90% automated coverage.
- Prefer well-supported open-source libraries (Typer, rich progress bars, etc.) over bespoke implementations.

## Getting Started
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev] -c constraints.txt
```

Run the (placeholder) CLI:
```bash
lf2x version
lf2x configure --output-dir dist/demo
```

## Development Workflow
- `pytest` executes the TDD suite with coverage enforcement (`--cov-fail-under=90`).
- `ruff` and `ruff format` enforce linting/formatting.
- `mypy` enforces strict typing across `src/lf2x`.
- `vulture` helps detect unused code paths.
- `pre-commit install` wires the quality gates locally; CI mirrors these checks.

## Repository Layout
```
src/lf2x/        # Library code and CLI entry points
cli/             # CLI scaffolding artifacts (non-library helpers)
tests/           # Unit and CLI smoke tests
mappings/        # Component mapping data (placeholders during v0.0.1)
docs/            # Product requirements and development plan
```

## Community
- See `CONTRIBUTING.md` for contribution workflow.
- Reference `CODE_OF_CONDUCT.md` for behavior expectations.
- Review `SECURITY.md` for vulnerability disclosure guidance.

LF2X is released under the MIT License.
