## 4.2.3 - Pytest/secondary-video configuration alignment

- Fixed the secondary WebM default mismatch that caused CI to fail: VP9 now defaults to CRF 0, emitting `-lossless 1` as required by the lossless-output policy.
- Synchronized `config/app.toml`, `config/settings.py`, `config/loader.py`, and the performance test with the lossless WebM default.
- Kept source resolution and FPS unmodified (`0` means no scaling/FPS override) and retained 256 kb/s Opus audio.


## 4.1.1 - Ruff compatibility and code-quality cleanup

- Fixed Ruff import ordering, unused imports and modernized Python 3.11 type annotations.
- Replaced deprecated `subprocess` pipe handling with `capture_output` where applicable.
- Added explicit `strict=True` to the media fingerprint `zip()` call.
- Removed the exact Ruff version requirement; development environments now accept Ruff `>=0.9,<0.17`.
- Preserved the duplicate-media detection and context-aware processed-video renaming behavior.


## Unreleased

- Added a rename-only migration path for ZIPs that were already processed: when a previously processed duplicate is supplied again, the pipeline extracts it only to re-infer the filename metadata, renames the existing output folder/artifacts, updates manifests/registries, and does not rerun FFmpeg, Whisper or translation.
- Exact media duplicates now use a SHA-256 fast path before expensive FFmpeg identity sampling, including when the duplicate has a different filename.
- Removed the extra FFmpeg audio-stream validation pass that was executed before every conversion.
- Replaced the generated MP3 companion artifact with a WebM secondary video using VP9 lossless video by default, preserving source resolution/FPS and using high-quality 256 kb/s Opus audio. Historical MP3 outputs remain resumable and are not deleted by the migration.
- Switched the default H.264 preset from `medium` to `veryfast` to prioritize throughput for CPU-based batch conversion.
- Added content-aware media deduplication for similarly named files across different ZIP sources. Exact SHA-256 matches are treated as duplicates; strong matches additionally compare duration, dimensions and sampled video/audio fingerprints.
- Persisted media identities in `storage/state/media_registry.jsonl` so duplicate decisions survive later runs.
- Output collision suffixes now derive from media content rather than the ZIP-relative path, preventing needless name changes when the same media arrives through another archive path.
- Improved filename context resolution to use meaningful ZIP/directory names while ignoring `wetransfer`/`drive-download` transport noise.
- Ruff is now constrained to the compatible `<0.17` major range instead of a single patch release.
- FFmpeg conversions now emit periodic progress logs instead of appearing silent during long operations.

# Changelog

## v5.0.0 - unattended cloud execution

- Google Drive now performs a silent OAuth refresh check during every preflight when a refresh token exists.
- Scheduled mode never starts an interactive OAuth flow.
- rclone remotes are health-checked with a read-only listing before unattended processing; this lets rclone refresh OAuth tokens automatically when the backend supports refresh.
- Multiple rclone remotes remain stored in one isolated `rclone.conf`; switching provider does not delete previous remotes.
- Added optional rclone binary auto-update check/upgrade, disabled by default for scheduler stability.
- Added explicit provider `verify` command for administrators.
- Added Windows Task Scheduler installation script using the executable directory as working directory.
- Added scheduler/unattended documentation and recovery procedures.

# Changelog

## [4.0.0] - 2026-08-21

### Added
- Unattended execution contract with `run --scheduled`.
- Double-click behavior for the compiled executable: no arguments means scheduled execution.
- Persistent active-provider runtime with source, target, profile and Google archive location.
- One-time `provider setup-google` flow combining OAuth and folder configuration.
- One-time `provider setup-rclone` flow combining remote authentication and active location configuration.
- Cross-platform execution lock at `storage/state/run.lock`.
- Unattended readiness checks that never start an OAuth browser flow.
- Frozen executable root resolution so PyInstaller builds keep `config`, `secrets` and `storage` beside the executable.
- Dedicated documentation for Windows Task Scheduler, cron/systemd and credential lifecycle.

### Changed
- Scheduled execution no longer hardcodes Google Drive.
- Switching provider preserves previous credentials/remotes instead of deleting them.
- Google token persistence and refresh are explicitly treated as installation state, not runtime interaction.
- rclone configuration remains outside the executable and is reused by every scheduled execution.

### Security
- OAuth credentials are never bundled in PyInstaller output.
- `rclone.conf`, Google tokens and runtime provider selection remain untracked.
- Provider failures in scheduled mode return `not_ready` instead of opening interactive authentication.
