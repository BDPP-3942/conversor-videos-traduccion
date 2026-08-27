import subprocess
from pathlib import Path

from config.settings import AppSettings
from src.ffmpeg_resolver import FFmpegResolver
from src.media_identity import MediaIdentityResolver


def _make_video(path: Path, color: str = "blue") -> None:
    subprocess.run(
        [
            str(FFmpegResolver.resolve(AppSettings())),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=160x90:r=5",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:sample_rate=8000",
            "-t",
            "2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )


def test_identity_resolver_uses_integrated_ffmpeg_by_default() -> None:
    resolver = MediaIdentityResolver()

    assert resolver.ffmpeg_bin == FFmpegResolver.resolve(AppSettings())


def test_exact_duplicate_is_detected_after_name_candidate(tmp_path: Path) -> None:
    first = tmp_path / "07º Opt Taich Bombeos.mp4"
    second = tmp_path / "7º OPT TAICH BOMBEOS.mp4"
    _make_video(first)
    second.write_bytes(first.read_bytes())

    resolver = MediaIdentityResolver(FFmpegResolver.resolve(AppSettings()))
    identity = resolver.build_identity(first)
    match = resolver.find_duplicate(
        second,
        "7º OPT TAICH BOMBEOS",
        [
            {
                "status": "success",
                "source": "first.zip/video.mp4",
                "output_folder": "37x07_Bombeos",
                "normalized_name": "7 opt taich bombeos",
                **identity.to_dict(),
            }
        ],
    )

    assert match is not None
    assert match.status == "duplicate_exact"
    assert match.score == 1.0


def test_same_name_but_different_video_is_not_skipped(tmp_path: Path) -> None:
    first = tmp_path / "bombeos_a.mp4"
    second = tmp_path / "bombeos_b.mp4"
    _make_video(first, "blue")
    _make_video(second, "red")

    resolver = MediaIdentityResolver(FFmpegResolver.resolve(AppSettings()))
    identity = resolver.build_identity(first)
    match = resolver.find_duplicate(
        second,
        "7º OPT TAICH BOMBEOS",
        [
            {
                "status": "success",
                "source": "first.zip/video.mp4",
                "output_folder": "37x07_Bombeos",
                "normalized_name": "7 opt taich bombeos",
                **identity.to_dict(),
            }
        ],
    )

    assert match is None


def test_different_visual_content_is_not_duplicate(tmp_path: Path) -> None:
    first = tmp_path / "bombeos_blue.mp4"
    second = tmp_path / "bombeos_red.mp4"
    _make_video(first, "blue")
    _make_video(second, "red")

    resolver = MediaIdentityResolver(FFmpegResolver.resolve(AppSettings()))
    identity = resolver.build_identity(first)
    match = resolver.find_duplicate(
        second,
        "7 opt taich bombeos",
        [
            {
                "status": "success",
                "source": "first.zip/video.mp4",
                "output_folder": "37x07_Bombeos",
                "normalized_name": "7 opt taich bombeos",
                **identity.to_dict(),
            }
        ],
    )

    assert match is None
