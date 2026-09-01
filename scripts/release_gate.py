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
    # Arguments are passed as an argv list (never through a shell); the callers
    # below use only fixed git subcommands and validated release metadata.
    return subprocess.check_output(  # noqa: S603
        [git_executable, *args],
        text=True,
    ).strip()


def _fail(message: str) -> None:
    print(f"RELEASE GATE: FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    expected_sha = sys.argv[1] if len(sys.argv) > 1 else ""
    expected_version = sys.argv[2] if len(sys.argv) > 2 else "1.5.0"

    actual_sha = _git("rev-parse", "HEAD")
    if expected_sha and actual_sha != expected_sha:
        _fail(f"checked-out SHA {actual_sha} differs from PR HEAD SHA {expected_sha}")

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject.get("project", {}).get("version")
    if not isinstance(version, str):
        _fail("pyproject.toml has no static project.version")
    if version != expected_version:
        _fail(f"pyproject version is {version}, expected {expected_version}")

    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    heading = rf"^## \[{re.escape(expected_version)}\](?:\s|$)"
    if not re.search(heading, changelog, re.MULTILINE):
        _fail(f"CHANGELOG.md has no {expected_version} release heading")

    releases = Path("docs/RELEASES.md").read_text(encoding="utf-8")
    if expected_version not in releases:
        _fail(f"docs/RELEASES.md does not mention {expected_version}")

    context_files = sorted(Path("config").glob("palabras_contexto.*"))
    if not context_files:
        _fail("no config/palabras_contexto.* source resource exists")
    print("Context resources:", ", ".join(path.as_posix() for path in context_files))

    tag_ref = f"refs/tags/v{expected_version}"
    remote_refs = _git("ls-remote", "--tags", "origin", tag_ref)
    if remote_refs:
        _fail(f"release tag v{expected_version} already exists on origin")

    print("RELEASE GATE: PASS")
    print(f"SHA: {actual_sha}")
    print(f"Version: {version}")
    print(f"Tag v{expected_version}: absent")


if __name__ == "__main__":
    main()
