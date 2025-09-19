# Contributing to LF2X

Thanks for your interest in improving LF2X! We welcome pull requests and issues from the community. This guide outlines how to get set up and the standards we expect contributions to meet.

## Development Environment
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -e .[dev] -c constraints.txt
   pre-commit install
   ```
3. Run the test suite with coverage:
   ```bash
   pytest
   ```

## Quality Expectations
- Follow Test-Driven Development where practical; maintain ≥90% coverage (`pytest` enforces this).
- Run `ruff`, `mypy`, and `vulture` before submitting a PR.
- Keep generated artifacts outside the repository tree (`dist/` by default) and ensure CLI options allow overrides.
- Prefer widely adopted OSS libraries for CLI scaffolding, progress bars, etc., rather than bespoke implementations.
- Honour SOLID, DRY, and KISS principles—code should be easy to read and extend.

## Pull Request Checklist
- [ ] Tests pass locally with coverage ≥90%.
- [ ] `ruff`, `mypy`, and `vulture` report no issues.
- [ ] Documentation and changelog entries (if required) are updated.
- [ ] Added or updated TODOs are actionable and referenced in conversion reports when necessary.

## Reporting Issues
Use GitHub issues and include:
- LF2X version (`lf2x version`)
- Python version (`python --version`)
- Steps to reproduce
- Expected vs. actual behaviour, including any relevant logs or configuration files

## Code of Conduct
All contributors must follow the project [Code of Conduct](CODE_OF_CONDUCT.md).

We appreciate your contributions—thank you for helping LF2X grow!
