# Contributing and repository governance

## Branches

Use short-lived branches with one of these prefixes:

- `feature/*` — new functionality.
- `fix/*` — bug fixes and robustness corrections.
- `security/*` — security changes.
- `docs/*` — documentation-only changes.
- `release/*` — release preparation.
- `main` — protected integration and release history.

Avoid ad-hoc prefixes and issue-title branches. Prefer one logical change per branch and delete merged branches promptly.

## Commit messages

Use Conventional Commit-style subjects:

- `feat:` — new functionality.
- `fix:` — bug fix.
- `refactor:` — behavior-preserving structural change.
- `test:` — tests only.
- `docs:` — documentation only.
- `ci:` — CI/workflow changes.
- `build:` — packaging/build/dependency changes.
- `security:` — security hardening or security-specific fixes.
- `perf:` — performance improvements.

Keep the subject imperative, specific, and concise. Do not use `debug:`, `temp:`, `wip:`, or personal/local-state messages for changes intended to remain in repository history.

## Pull requests

Every PR should contain these sections:

1. **Objetivo** — what the change is intended to accomplish.
2. **Problema** — current behavior or limitation.
3. **Solución** — implementation and architectural impact.
4. **Tests** — tests executed and their relevant results.
5. **CI** — required GitHub Actions checks and final status.
6. **Riesgos** — regressions, compatibility concerns, operational risks, and known limitations.

Do not merge a PR when its required CI is failing or when the description does not provide enough evidence to review the change.

## Repository hygiene

Do not commit:

- debug files;
- temporary or one-off workflows;
- credentials, API keys, tokens, private configuration, or provider profiles;
- local runtime artifacts;
- generated binaries or downloaded model/tool assets;
- build outputs, caches, logs, or editor metadata.

Use `.gitignore` for local-only state and keep safe configuration templates such as `.env.example` free of real credentials.

## CI and workflows

CI is validation, not a mechanism for mutating feature branches. Formatting should be enforced by checks. Avoid workflows that automatically commit generated or reformatted files back to developer branches unless there is an explicit, documented repository policy requiring it.

Keep workflow permissions least-privilege (`contents: read` unless a workflow genuinely needs write access).

## Releases and tags

Release tags use semantic versioning with the `v` prefix, for example `v1.3.0`.

A published release tag identifies one immutable point in repository history. Never move or reuse an existing release tag for another commit. If a release must be corrected, publish a new patch version (for example `v1.3.1`).

Release notes should identify the release commit and the PRs or changes included in the release. Keep `CHANGELOG.md` aligned with published releases.

## Merge strategy

Prefer squash merging for short-lived feature/fix/docs/security branches when the PR represents one logical change. The resulting commit on `main` should retain a Conventional Commit-style subject. Use a regular merge commit only when preserving branch topology has a deliberate value; avoid rebase-merging when it obscures the review-to-release relationship.

## Governance principle

`main` is the authoritative integration and release line. Feature branches are disposable working refs, not permanent history. Release tags are historical anchors and must remain stable.
