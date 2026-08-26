from __future__ import annotations

import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileSystemLimits:
    """Effective conservative limits for the filesystem hosting a path."""

    max_component: int
    max_path: int | None
    platform: str
    source: str


def _windows_limits(path: Path) -> FileSystemLimits:
    max_component = 255
    max_path = 260
    source = "Windows conservative MAX_PATH"

    try:
        import ctypes
        import ctypes.wintypes as wintypes

        root = Path(path).resolve().anchor or "C:\\"
        volume = ctypes.create_unicode_buffer(261)
        filesystem = ctypes.create_unicode_buffer(261)
        serial = wintypes.DWORD()
        max_component_length = wintypes.DWORD()
        flags = wintypes.DWORD()
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(root),
            volume,
            len(volume),
            ctypes.byref(serial),
            ctypes.byref(max_component_length),
            ctypes.byref(flags),
            filesystem,
            len(filesystem),
        )
        if ok and max_component_length.value:
            max_component = int(max_component_length.value)
            source = f"Windows volume {filesystem.value or 'unknown'}"
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        logger.debug("Unable to query Windows volume limits for %s: %s", path, exc)

    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
        ) as key:
            enabled, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
        if int(enabled) == 1:
            max_path = 32767
            source += "; LongPathsEnabled=1"
    except (AttributeError, OSError, TypeError, ValueError) as exc:
        logger.debug("Unable to query Windows long-path policy: %s", exc)

    return FileSystemLimits(max_component, max_path, "windows", source)


def get_filesystem_limits(path: Path) -> FileSystemLimits:
    """Return limits for the filesystem containing *path* without hard-coding OS values."""
    if sys.platform == "win32":
        return _windows_limits(path)

    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent

    max_component = 255
    max_path: int | None = None
    source = "POSIX pathconf"
    try:
        max_component = int(os.pathconf(probe, "PC_NAME_MAX"))
    except (AttributeError, OSError, ValueError):
        pass
    try:
        max_path = int(os.pathconf(probe, "PC_PATH_MAX"))
    except (AttributeError, OSError, ValueError):
        pass
    return FileSystemLimits(max_component, max_path, "posix", source)


def _truncate_by_utf8_bytes(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    result: list[str] = []
    used = 0
    for char in value:
        size = len(char.encode("utf-8"))
        if used + size > max_bytes:
            break
        result.append(char)
        used += size
    return "".join(result)


def fit_component(name: str, parent: Path, *, suffix: str = "") -> str:
    """Fit a filename/directory component to the actual host filesystem."""
    limits = get_filesystem_limits(parent)
    max_component = max(1, limits.max_component)
    requested = f"{name}_{suffix}" if suffix else name
    if len(requested.encode("utf-8")) <= max_component:
        candidate = requested
    else:
        suffix_bytes = len(suffix.encode("utf-8"))
        separator_bytes = 1 if suffix else 0
        budget = max(1, max_component - suffix_bytes - separator_bytes)
        prefix = _truncate_by_utf8_bytes(name, budget).rstrip(" .")
        candidate = f"{prefix}_{suffix}" if suffix else prefix

    if limits.max_path is not None:
        parent_len = len(str(parent.resolve()).encode("utf-8"))
        available = limits.max_path - parent_len - 1
        if available > 0 and len(candidate.encode("utf-8")) > available:
            suffix_bytes = len(suffix.encode("utf-8"))
            suffix_total = suffix_bytes + (1 if suffix else 0)
            if suffix and available > suffix_total:
                prefix_budget = available - suffix_total
                prefix = _truncate_by_utf8_bytes(name, prefix_budget).rstrip(" .")
                candidate = f"{prefix}_{suffix}" if prefix else suffix[: max(1, available - 1)]
            else:
                candidate = _truncate_by_utf8_bytes(candidate, available).rstrip(" .")

    return candidate or "_"


def path_is_within_limit(path: Path) -> bool:
    limits = get_filesystem_limits(path.parent)
    encoded = str(path).encode("utf-8")
    component_ok = all(
        len(component.encode("utf-8")) <= limits.max_component
        for component in path.parts
        if component not in {path.anchor, ""}
    )
    path_ok = limits.max_path is None or len(encoded) <= limits.max_path
    return component_ok and path_ok


_WINDOWS_RESERVED = re.compile(
    r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$",
    re.IGNORECASE,
)
