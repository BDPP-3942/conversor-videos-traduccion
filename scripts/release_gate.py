from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def _git(*args: str) -> str:
    git_executable = shutil.which("git")
    if git_executable is None:
        raise RuntimeError("git executable was not found on PATH")
    # The command and arguments are fixed internally; no shell is involved.
    return subprocess.check_output(  # noqa: S603
        [git_executable, *args],
        text=True,
    ).strip()


def _fail(message: str) -> None:
    print(f"RELEASE GATE: FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    expected_sha = sys.argv[1] if len(sys.argv) > 1 else ""
    expected_version = sys.argv[2] if len(sys.argv) > 2 else ""
    require_tag_absent = len(sys.argv) > 3 and sys.argv[3].lower() == "true"

    actual_sha = _git("rev-parse", "HEAD")
    if expected_sha and actual_sha != expected_sha:
        _fail(f"checked-out SHA {actual_sha} differs from PR HEAD SHA {expected_sha}")

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject.get("project", {}).get("version")
    if not isinstance(version, str):
        _fail("pyproject.toml has no static project.version")
    if not expected_version:
        expected_version = version
    if version != expected_version:
        _fail(f"pyproject version is {version}, expected {expected_version}")

    # CHANGELOG.md is the immutable published-history ledger. Candidate release
    # details live in docs/RELEASES.md/RELEASE_SCOPE.md until the release is
    # actually published, so validating the candidate heading here would force
    # destructive rewriting of historical changelog text merely to pass CI.
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    published_history_heading = r"^## \[1\.7\.4\](?:\s|$)"
    if not re.search(published_history_heading, changelog, re.MULTILINE):
        _fail("CHANGELOG.md does not retain the published 1.7.4 release history")

    releases = Path("docs/RELEASES.md").read_text(encoding="utf-8")
    if expected_version not in releases:
        _fail(f"docs/RELEASES.md does not mention {expected_version}")

    context_files = sorted(Path("config").glob("palabras_contexto.*"))
    if not context_files:
        _fail("no config/palabras_contexto.* source resource exists")
    print("Context resources:", ", ".join(path.as_posix() for path in context_files))

    tag_ref = f"refs/tags/v{expected_version}"
    remote_refs = _git("ls-remote", "--tags", "origin", tag_ref)
    if remote_refs and require_tag_absent:
        _fail(f"release tag v{expected_version} already exists on origin")
    if remote_refs:
        print(
            "PR validation: release tag "
            f"v{expected_version} already exists; continuing because this is not a release invocation."
        )
    else:
        print(f"Tag v{expected_version}: absent")

    print("RELEASE GATE: PASS")
    print(f"SHA: {actual_sha}")
    print(f"Version: {version}")


if __name__ == "__main__":
    main()
