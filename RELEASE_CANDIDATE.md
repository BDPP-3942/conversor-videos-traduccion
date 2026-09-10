# Release Candidate — 1.8.0

## Release

- **Version:** 1.8.0
- **Previous published release:** `v1.7.4` — published on 8 September 2026.
- **Target tag:** `v1.8.0` — pending final CI, Release Gate and merge validation.
- **Candidate SHA:** must be the exact final `main` SHA after all release PRs are merged and validated.

`v1.7.4` is already a published GitHub Release. It is historical state, not a candidate, and its tag must not be recreated or moved.

## Release classification

`1.8.0` is a MINOR release. The combined scope introduces compatible functionality rather than only corrective maintenance.

## Scope

- Separate Whisper VAD silence (`1500 ms`) from subtitle split silence (`750 ms`).
- Retry suspicious STT segments without the large initial prompt or previous-text context.
- Preserve numeric `clip_timestamps` for selective recovery.
- Upgrade the local Spanish→English fallback to pinned MADLAD-400 3B CT2 INT8.
- Use MADLAD's shared SentencePiece tokenizer and `<2en>` target prefix.
- Enforce a 3,000,000,000-byte installation budget and validate required model artifacts.
- Keep local model auto-download disabled by default.
- Complete the uv migration for development, CI, packaging and dependency auditing while preserving pip wheel compatibility.

## Dependency audit

The audit environment is resolved from the versioned `uv.lock` file. The editable local project package is removed before the audit so `pip-audit` audits the PyPI-resolvable dependency graph rather than the source checkout itself.

The CI command is:

```bash
uv run --locked --no-sync --group audit pip-audit --strict
```

Both the base/Google and TTS audit jobs use the same principle.

## Validation

Required before publication:

- Linux, Windows and macOS.
- Python 3.11, 3.12 and 3.13.
- Full pytest suite.
- Ruff lint/security/format and `compileall`.
- `uv lock --check`, locked sync and `uv pip check`.
- Packaging, clean wheel installation and entry points.
- Dependency audits.
- Release Gate on the exact final SHA.
- Real MADLAD model preparation/benchmark on the target hardware.

## Version consistency

The release version must agree in:

- `pyproject.toml` → `1.8.0`.
- `config/app.toml` → `1.8.0`.
- `CHANGELOG.md` → published `1.7.4` retained as history plus a new `1.8.0` entry before publication.
- `docs/RELEASES.md` → published `1.7.4` plus candidate `1.8.0`.
- `docs/VERSIONING.md` → published `1.7.4` plus candidate `1.8.0`.
- `RELEASE_SCOPE.md` → `1.8.0`.
- This file → `1.8.0`.
- `uv.lock` → project package metadata synchronized to `1.8.0` after the branch is rebased onto the final uv-migration base.

## Decision

**Do not merge or create `v1.8.0` until the final candidate SHA is green in CI and Release Gate.** After merge, validate `main` again and create the immutable `v1.8.0` tag/release on that exact SHA.
