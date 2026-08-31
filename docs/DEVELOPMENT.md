# Development guide

## Environment

The supported Python range is `>=3.11,<3.14`.

For development:

```bash
python -m pip install -e ".[dev]"
```

Add optional extras only when the feature being developed needs them, for example `[google]`, `[tts]` or `[package]`.

## Project layout

```text
config/       configuration loading and settings
src/          application modules and adapters
tests/        automated tests
scripts/      setup, execution, scheduling and packaging helpers
docs/         technical documentation
storage/      runtime input/output/state directories
tools/        external runtime resources
```

## Change workflow

1. Identify the existing pipeline abstraction responsible for the change.
2. Avoid duplicating provider/storage business logic in wrappers.
3. Update configuration/CLI only when the implementation actually exposes the change.
4. Add deterministic tests.
5. Update the canonical documentation.
6. Run the local quality checks and inspect CI.
7. If the change is released, record it in `CHANGELOG.md` and `docs/RELEASES.md` with evidence tied to the release/tag.

## Documentation rule

Do not document an option, command, path or feature unless it can be verified against the current code, configuration or tests. Prefer `--help` output and source definitions over historical documentation.
