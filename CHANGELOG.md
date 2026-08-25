## Unreleased
- `reprocess-subtitles` admite ahora ámbito concreto y general: con `--output-folder`, `--video` o `--source` reprocesa una salida; sin selector o con `--all` recorre todas las salidas existentes elegibles. El modo sigue siendo STT-only, translate-only o completo.
- El reprocesado general aísla los errores por carpeta, continúa con las demás y devuelve un resumen global del lote.

- La deduplicación de resultados locales se ejecuta automáticamente al finalizar `run`; `--delete` deja de ser necesario.
- `dedupe-output` aplica por defecto la limpieza y conserva `--dry-run` como modo explícito de simulación.
- Añadido `reprocess-subtitles` con modos STT-only, translate-only y completo sobre carpetas existentes, sin competir con la deduplicación ni generar sufijos por colisión.
- El reprocesado reutiliza MP4/WebM existentes, valida VTT/timestamps antes del reemplazo, conserva backups versionados y registra cada operación en `reprocess_history/`.
- Añadida resolución del resultado por carpeta, vídeo o `source` de manifest, junto con el diagnóstico de gaps/solapamientos de timestamps para separar problemas de STT/VAD de los de traducción.
- Añadido el comando `prefetch-whisper` usado por los scripts de instalación y ajustado PyInstaller para incluir las dependencias cargadas dinámicamente.
- Corregidos scripts shell con finales de línea CRLF que impedían la validación `bash -n`, incluido `install_launchd.sh`.
- Los tests de reprocesado ya no dependen de un archivo externo al repositorio ni de ningún artefacto externo al repositorio; el caso de ZIP estructuralmente duplicado es autocontenido.
- El reprocesado queda expuesto también mediante wrappers locales, desatendidos y ejecutables PyInstaller; `run_local`, `run_scheduled` y `run_unattended` pueden despachar `reprocess-subtitles`.
- `reprocess-subtitles --scheduled` usa el proveedor/target persistidos y permite ejecución no interactiva en Task Scheduler/launchd.
- `install_task_scheduler.ps1` y `install_launchd.sh` aceptan argumentos de comando para instalar tareas de reprocesado específicas.

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

## Checks after general reprocess scope

- `reprocess-subtitles` supports concrete selection (`--output-folder`, `--video`, `--source`) and general selection (`--all` or no selector).
- No selector now means all eligible existing output folders.
- `--stt-only` affects transcription only; `--translate-only` affects translation only; without either, both are regenerated.
- General reprocesado continues after per-folder failures and returns an aggregate summary.
