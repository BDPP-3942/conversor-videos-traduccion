# Use cases

## UC-01 — Process a local batch

1. Place supported video/ZIP input in `storage/input/`.
2. Run `python main.py doctor`.
3. Run `python main.py run`.
4. Inspect validated output in `storage/output/`.

## UC-02 — Process cloud-backed input

Configure a Google Drive or rclone provider, select it as the active provider, verify credentials, then run the same common pipeline. Scheduled mode uses the persisted provider profile without interactive authentication.

## UC-03 — Recover subtitles without regenerating media

Use `reprocess-subtitles` when an existing output has a missing/invalid original or translated VTT. The recovery layer selectively reruns STT and/or translation and leaves the normal video untouched.

## UC-04 — Generate synchronized TTS

Enable TTS, provide the Kokoro model/voice assets and run the normal pipeline. TTS consumes the validated translated VTT and produces cue-timed audio plus configured MP4/WebM outputs.

## UC-05 — Inspect and remove duplicates

Run `duplicates scan`, then `duplicates analyze`, review the persisted plan, and only then run `duplicates delete`. `--dry-run` is available for the deletion phase.

## UC-06 — Run unattended

Complete provider authentication administratively, verify readiness, then schedule `run --scheduled`. The scheduled process must have deterministic working paths, credentials, models and write permissions.
