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
    return subprocess.check_output([git_executable, *args], text=True).strip()  # noqa: S603


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
    if remote_refs and require_tag_absent:
        _fail(f"release tag v{expected_version} already exists on origin")
    if remote_refs:
        print(f"PR validation: release tag v{expected_version} already exists; continuing because this is not a release invocation.")
    else:
        print(f"Tag v{expected_version}: absent")

    print("RELEASE GATE: PASS")
    print(f"SHA: {actual_sha}")
    print(f"Version: {version}")


if __name__ == "__main__":
    main()
