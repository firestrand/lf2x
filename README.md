# LF2X

LangFlow to X (LF2X) converts LangFlow visual workflows into production-grade LangGraph and LangChain projects. The repository houses the conversion engine, CLI tooling, and supporting documentation.

## Key Principles
- Keep the core library under `src/lf2x` and write generated artifacts outside the repo (default `dist/<flow-id>`).
- Maintain strict quality gates: `ruff`, `mypy`, `pytest --cov`, and ≥90% automated coverage.
- Prefer well-supported OSS packages (Typer, HTTPX, etc.) over bespoke implementations.

## Getting Started
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev] -c constraints.txt
```

## CLI Overview
```bash
# Inspect installed version
lf2x version

# Show resolved configuration (CLI > config file > defaults)
lf2x configure --output-dir dist/demo --config ./lf2x.yaml

# Convert a LangFlow JSON export (writes project + reports under dist/<flow-id>)
lf2x convert flow.json --output-dir dist --overwrite

# Analyze a flow without generating code
lf2x analyze flow.json --output-dir dist

# Validate that a flow parses and returns a recommended target
lf2x validate flow.json
```

When `LF2X_LANGFLOW_BASE_URL` (and optional `LF2X_LANGFLOW_API_TOKEN`) are exported, the tooling can fetch flows directly from a running LangFlow instance via the REST client.

## Development Workflow
- `pytest` runs unit, CLI, and integration suites (`LF2X_LANGFLOW_BASE_URL` enables live LangFlow tests).
- `ruff`/`ruff format` enforce linting and formatting.
- `mypy` provides strict typing guarantees.
- `pre-commit install` wires the quality gates locally; CI mirrors these checks.

## Repository Layout
```
src/lf2x/        # Library code and CLI entry points
cli/             # Templates/helpers for generated CLIs
tests/           # Unit, CLI, and integration tests
mappings/        # Component mapping data/fixtures
docs/            # Product requirements and development plan
```

## Community
- `CONTRIBUTING.md` documents the contribution workflow.
- `CODE_OF_CONDUCT.md` governs expected behavior.
- `SECURITY.md` outlines vulnerability disclosure guidance.

LF2X is released under the MIT License.
