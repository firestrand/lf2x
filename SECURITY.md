# Security Policy

We take security seriously and appreciate disclosures of vulnerabilities.

## Supported Versions
LF2X is under active development. Security fixes are applied to the latest release (starting with `v0.0.1`) and the `main` branch.

## Reporting a Vulnerability
- Email the maintainers or create a git issue with a description of the vulnerability, reproduction steps, and potential impact.
- Expect a response within 3 business days. If you do not receive confirmation, please follow up.
- Do not disclose vulnerabilities publicly until we have had a reasonable opportunity to investigate and release a fix.

## Security Best Practices
- Avoid committing secrets to the repository. Generated artifacts should store secrets in `.env` files located outside the codebase.
- Use the provided tooling (`ruff`, `mypy`, `vulture`, `pytest`) before pushing changes—they help prevent classes of security and quality issues.
- Keep dependencies up to date by relying on `constraints.txt` and review updates in pull requests.
