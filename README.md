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

## Validating Converted Projects
1. Convert a flow JSON export:
   ```bash
   lf2x convert tests/fixtures/flows/simple_passthrough.json \
       --output-dir dist/manual --overwrite
   ```
   This creates a scaffold under `dist/manual/simple_passthrough/` with tests, config, CLI, and conversion reports.
2. Run the generated tests inside the scaffold:
   ```bash
   cd dist/manual/simple_passthrough
   pytest
   ```
3. Inspect reports/TODOs:
   - `conversion_report.md` and `.json` summarize file statuses and outstanding TODO markers.
   - `.env.example` lists any secrets detected during conversion.
4. (Optional) Re-run analysis/validation directly from the CLI:
   ```bash
   lf2x analyze tests/fixtures/flows/simple_passthrough.json
   lf2x validate tests/fixtures/flows/simple_passthrough.json
   ```

## Running Generated Projects
The conversion summary prints the generated package name (e.g., `package=simple_passthrough`). From the scaffold root you can invoke the packaged CLI:

```bash
cd dist/manual/simple_passthrough
PYTHONPATH=src python -m simple_passthrough.cli --help
PYTHONPATH=src python -m simple_passthrough.cli --message "Hello from LF2X"
```

The module name matches the slugified flow name reported by `lf2x convert`. Setting `PYTHONPATH=src` ensures Python can import the generated package without installing it. Adjust the command if you generated multiple flows under the same `dist/` directory.

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
