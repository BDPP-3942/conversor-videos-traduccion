from __future__ import annotations

import csv
import html
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

MAX_PROMPT_FILE_BYTES = 2 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".docx"}
AUTO_CONTEXT_NAMES = tuple(f"palabras_contexto{extension}" for extension in sorted(SUPPORTED_EXTENSIONS))


def _candidate_path(value: str, base_dir: Path | None) -> Path | None:
    raw = Path(value).expanduser()
    candidates = [raw] if raw.is_absolute() else []
    if base_dir is not None:
        candidates.append(base_dir / raw)
    candidates.append(Path.cwd() / raw)
    candidates.append(Path(__file__).resolve().parents[1] / raw)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _find_generic_context_file(base_dir: Path | None) -> Path | None:
    roots = [item for item in (base_dir, Path.cwd(), Path(__file__).resolve().parents[1]) if item]
    for root in roots:
        for name in AUTO_CONTEXT_NAMES:
            candidate = (root / name).resolve()
            if candidate.is_file():
                return candidate
    return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _read_csv(path: Path) -> str:
    rows: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            rows.extend(cell.strip() for cell in row if cell.strip())
    return ", ".join(rows)


def _read_docx(path: Path) -> str:
    try:
        with ZipFile(path, "r") as archive:
            members = {item.filename: item for item in archive.infolist()}
            document = members.get("word/document.xml")
            if document is None:
                raise ValueError("DOCX does not contain word/document.xml")
            if document.file_size > MAX_PROMPT_FILE_BYTES:
                raise ValueError("DOCX document.xml exceeds the prompt file size limit")
            payload = archive.read(document)
    except (BadZipFile, KeyError) as exc:
        raise ValueError(f"Invalid DOCX context file: {path}") from exc

    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("DOCX XML with DTD/entity declarations is not accepted")
    decoded = payload.decode("utf-8", errors="strict")
    fragments = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", decoded, flags=re.DOTALL)
    return " ".join(html.unescape(fragment).strip() for fragment in fragments if fragment.strip())


def _read_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Whisper context path is not a regular file: {path}")
    if path.stat().st_size > MAX_PROMPT_FILE_BYTES:
        raise ValueError(f"Whisper context file exceeds {MAX_PROMPT_FILE_BYTES} bytes: {path}")
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return _read_text(path)
    if suffix == ".csv":
        return _read_csv(path)
    if suffix == ".docx":
        return _read_docx(path)
    raise ValueError(f"Unsupported Whisper context file extension: {suffix}")


def resolve_initial_prompt(value: str, base_dir: Path | None = None) -> tuple[str, str]:
    """Resolve a literal prompt or a context file into Whisper's string prompt."""
    raw = str(value or "").strip()
    if not raw:
        path = _find_generic_context_file(base_dir)
        if path is None:
            return "", "literal"
    else:
        path = _candidate_path(raw, base_dir)
        if path is None:
            if Path(raw).suffix.lower() in SUPPORTED_EXTENSIONS or Path(raw).name.lower().startswith(
                "palabras_contexto."
            ):
                raise FileNotFoundError(f"Whisper context file not found: {raw}")
            return re.sub(r"\s+", " ", raw).strip(), "literal"

    text = _read_file(path)
    prompt = re.sub(r"\s+", " ", text).strip()
    if not prompt:
        raise ValueError(f"Whisper context file is empty: {path}")
    return prompt, str(path)
