from __future__ import annotations

import hashlib
import logging
import re
import struct
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import which
from typing import Any

from src.file_naming import normalize_comparison_key, normalized_name_similarity

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MediaIdentity:
    sha256: str
    size: int
    duration_seconds: float | None
    width: int | None
    height: int | None
    video_codec: str | None
    audio_codec: str | None
    audio_channels: int | None
    audio_sample_rate: int | None
    video_samples: tuple[str, ...]
    audio_samples: tuple[tuple[float, float, float], ...]
    media_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DuplicateMatch:
    status: str
    score: float
    registry_entry: dict[str, Any]
    reason: str


class MediaIdentityResolver:
    """Find strong duplicate candidates without decoding every media file unnecessarily."""

    NAME_THRESHOLD = 0.82
    DURATION_TOLERANCE_SECONDS = 1.5
    DURATION_RELATIVE_TOLERANCE = 0.005
    VISUAL_THRESHOLD = 0.91
    AUDIO_RELATIVE_TOLERANCE = 0.18

    def __init__(
        self,
        ffmpeg_bin: str = "",
        timeout_seconds: int = 300,
        name_threshold: float = NAME_THRESHOLD,
        duration_tolerance_seconds: float = DURATION_TOLERANCE_SECONDS,
        visual_threshold: float = VISUAL_THRESHOLD,
    ) -> None:
        self.ffmpeg_bin = ffmpeg_bin or which("ffmpeg") or "ffmpeg"
        self.timeout_seconds = max(15, int(timeout_seconds))
        self.name_threshold = max(0.0, min(1.0, float(name_threshold)))
        self.duration_tolerance_seconds = max(0.1, float(duration_tolerance_seconds))
        self.visual_threshold = max(0.5, min(1.0, float(visual_threshold)))

    def build_identity(self, path: Path) -> MediaIdentity:
        if not path.is_file():
            raise FileNotFoundError(f"Media source does not exist: {path}")
        sha256 = self._sha256(path)
        metadata = self._probe(path)
        video_samples = self._sample_video(path, metadata["duration_seconds"])
        audio_samples = self._sample_audio(path, metadata["duration_seconds"])
        return MediaIdentity(
            sha256=sha256,
            size=path.stat().st_size,
            duration_seconds=metadata["duration_seconds"],
            width=metadata["width"],
            height=metadata["height"],
            video_codec=metadata["video_codec"],
            audio_codec=metadata["audio_codec"],
            audio_channels=metadata["audio_channels"],
            audio_sample_rate=metadata["audio_sample_rate"],
            video_samples=tuple(video_samples),
            audio_samples=tuple(audio_samples),
            media_type="video" if metadata["width"] is not None else "audio",
        )

    def find_duplicate(
        self,
        path: Path,
        normalized_name: str,
        candidates: list[dict[str, Any]],
    ) -> DuplicateMatch | None:
        if not candidates:
            return None

        exact_name = normalize_comparison_key(normalized_name)
        relevant = [
            item
            for item in candidates
            if normalized_name_similarity(exact_name, normalize_comparison_key(str(item.get("normalized_name", ""))))
            >= self.name_threshold
        ]
        if not relevant:
            return None

        identity = self.build_identity(path)
        for candidate in relevant:
            if candidate.get("sha256") == identity.sha256:
                return DuplicateMatch(
                    status="duplicate_exact",
                    score=1.0,
                    registry_entry=candidate,
                    reason="Exact SHA-256 match after a high-similarity normalized-name candidate.",
                )

        best: DuplicateMatch | None = None
        for candidate in relevant:
            score, reasons = self._compare_identity(identity, candidate)
            if score >= 0.90:
                match = DuplicateMatch(
                    status="duplicate_probable",
                    score=score,
                    registry_entry=candidate,
                    reason="; ".join(reasons),
                )
                if best is None or match.score > best.score:
                    best = match
        return best

    def candidate_names(self, registry_entries: list[dict[str, Any]], normalized_name: str) -> list[dict[str, Any]]:
        normalized_name = normalize_comparison_key(normalized_name)
        return [
            item
            for item in registry_entries
            if normalized_name_similarity(
                normalized_name,
                normalize_comparison_key(str(item.get("normalized_name", ""))),
            )
            >= self.name_threshold
        ]

    def _compare_identity(self, current: MediaIdentity, candidate: dict[str, Any]) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        candidate_duration = _as_float(candidate.get("duration_seconds"))
        if current.duration_seconds is None or candidate_duration is None:
            return 0.0, []
        duration_tolerance = max(
            self.duration_tolerance_seconds,
            current.duration_seconds * self.DURATION_RELATIVE_TOLERANCE,
        )
        duration_delta = abs(current.duration_seconds - candidate_duration)
        if duration_delta <= duration_tolerance:
            score += 0.25
            reasons.append(f"duration within {duration_delta:.2f}s")
        else:
            return 0.0, []

        width = candidate.get("width")
        height = candidate.get("height")
        if current.width and current.height and int(width or 0) == current.width and int(height or 0) == current.height:
            score += 0.15
            reasons.append("same video dimensions")
        elif current.media_type == "video" and candidate.get("media_type") != "video":
            return 0.0, []

        video_score = _sample_similarity(
            current.video_samples,
            tuple(str(value) for value in candidate.get("video_samples", [])),
        )
        if current.media_type == "video":
            if video_score < self.visual_threshold:
                return 0.0, []
            score += 0.40 * video_score
            reasons.append(f"sampled video fingerprint similarity {video_score:.2f}")

        audio_score = _audio_similarity(
            current.audio_samples,
            tuple(tuple(float(v) for v in sample) for sample in candidate.get("audio_samples", [])),
        )
        if current.audio_samples and candidate.get("audio_samples"):
            if audio_score < 0.82:
                return 0.0, []
            score += 0.20 * audio_score
            reasons.append(f"sampled audio fingerprint similarity {audio_score:.2f}")
        else:
            score += 0.10

        if current.audio_channels and int(candidate.get("audio_channels") or 0) == current.audio_channels:
            score += 0.05
            reasons.append("same audio channel count")
        if current.audio_sample_rate and int(candidate.get("audio_sample_rate") or 0) == current.audio_sample_rate:
            score += 0.05
            reasons.append("same audio sample rate")
        return min(score, 1.0), reasons

    def _probe(self, path: Path) -> dict[str, Any]:
        command = [self.ffmpeg_bin, "-hide_banner", "-i", str(path)]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=min(self.timeout_seconds, 60),
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("Could not probe media metadata for %s: %s", path.name, exc)
            return {
                "duration_seconds": None,
                "width": None,
                "height": None,
                "video_codec": None,
                "audio_codec": None,
                "audio_channels": None,
                "audio_sample_rate": None,
            }
        text = result.stderr or ""
        duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
        duration = None
        if duration_match:
            hours, minutes, seconds = duration_match.groups()
            duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        video_match = re.search(r"Video:\s*([^,\s]+).*?,\s*(\d{2,5})x(\d{2,5})", text)
        audio_match = re.search(
            r"Audio:\s*([^,\s]+).*?(\d+) Hz.*?(mono|stereo|(?:\d+) channels?)",
            text,
            re.IGNORECASE,
        )
        audio_channels = None
        if audio_match:
            channel_text = audio_match.group(3).lower()
            channel_number = re.search(r"\d+", channel_text)
            audio_channels = (
                1
                if channel_text == "mono"
                else 2
                if channel_text == "stereo"
                else int(channel_number.group(0))
                if channel_number
                else None
            )
        audio_rate = int(audio_match.group(2)) if audio_match else None
        return {
            "duration_seconds": duration,
            "width": int(video_match.group(2)) if video_match else None,
            "height": int(video_match.group(3)) if video_match else None,
            "video_codec": video_match.group(1) if video_match else None,
            "audio_codec": audio_match.group(1) if audio_match else None,
            "audio_channels": audio_channels,
            "audio_sample_rate": audio_rate,
        }

    def _sample_video(self, path: Path, duration: float | None) -> list[str]:
        if duration is None:
            return []
        positions = _sample_positions(duration)
        fingerprints: list[str] = []
        for position in positions:
            command = [
                self.ffmpeg_bin,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{position:.3f}",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                "scale=32:32,format=gray",
                "-f",
                "rawvideo",
                "pipe:1",
            ]
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=True,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                return []
            fingerprints.append(_average_hash(result.stdout))
        return fingerprints

    def _sample_audio(self, path: Path, duration: float | None) -> list[tuple[float, float, float]]:
        if duration is None:
            return []
        positions = _sample_positions(duration)
        samples: list[tuple[float, float, float]] = []
        for position in positions:
            command = [
                self.ffmpeg_bin,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{position:.3f}",
                "-i",
                str(path),
                "-t",
                "1",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "8000",
                "-f",
                "s16le",
                "pipe:1",
            ]
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=True,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                return []
            samples.append(_audio_features(result.stdout))
        return samples

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()


def _sample_positions(duration: float) -> tuple[float, ...]:
    if duration <= 0:
        return (0.0,)
    margins = min(2.0, duration * 0.05)
    if duration <= margins * 2:
        return (max(0.0, duration / 2),)
    usable = duration - 2 * margins
    return tuple(margins + usable * ratio for ratio in (0.10, 0.30, 0.50, 0.70, 0.90))


def _average_hash(raw: bytes) -> str:
    if not raw:
        return ""
    pixels = list(raw)
    mean = sum(pixels) / len(pixels)
    bits = "".join("1" if value >= mean else "0" for value in pixels)
    return f"{mean / 255:.6f}:{bits}"


def _sample_similarity(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    scores = []
    for first, second in zip(left, right, strict=True):
        first_parts = first.split(":", 1)
        second_parts = second.split(":", 1)
        if len(first_parts) != 2 or len(second_parts) != 2:
            return 0.0
        if len(first_parts[1]) != len(second_parts[1]):
            return 0.0
        equal = sum(a == b for a, b in zip(first_parts[1], second_parts[1], strict=True))
        bit_score = equal / len(first_parts[1])
        try:
            mean_a = float(first_parts[0])
            mean_b = float(second_parts[0])
        except ValueError:
            return 0.0
        luminance_score = max(0.0, 1.0 - abs(mean_a - mean_b) / 0.25)
        scores.append(0.8 * bit_score + 0.2 * luminance_score)
    return sum(scores) / len(scores)


def _audio_features(raw: bytes) -> tuple[float, float, float]:
    if len(raw) < 4:
        return (0.0, 0.0, 0.0)
    values = [sample[0] / 32768.0 for sample in struct.iter_unpack("<h", raw[: len(raw) - (len(raw) % 2)])]
    if not values:
        return (0.0, 0.0, 0.0)
    mean_abs = sum(abs(value) for value in values) / len(values)
    rms = (sum(value * value for value in values) / len(values)) ** 0.5
    crossings = sum(1 for previous, current in zip(values, values[1:], strict=False) if (previous < 0) != (current < 0))
    return (mean_abs, rms, crossings / len(values))


def _audio_similarity(
    left: tuple[tuple[float, float, float], ...],
    right: tuple[tuple[float, float, float], ...],
) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    scores: list[float] = []
    for first, second in zip(left, right, strict=True):
        component_scores = []
        for a, b in zip(first, second, strict=True):
            denominator = max(abs(a), abs(b), 1e-6)
            component_scores.append(max(0.0, 1.0 - abs(a - b) / denominator))
        scores.append(sum(component_scores) / len(component_scores))
    return sum(scores) / len(scores)


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
