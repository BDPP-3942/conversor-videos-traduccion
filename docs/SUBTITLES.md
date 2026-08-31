# Subtitles and WebVTT

WebVTT is the subtitle interchange format between STT, translation, QA/repair and TTS.

## Temporal contract

The original VTT establishes the timing. Translation preserves `start` and `end`; TTS uses the translated validated VTT without shifting later cues.

A valid cue must have `start < end`, ordered timestamps and valid WebVTT syntax. Gaps between cues are valid and represent silence; they are not filled automatically.

## QA and repair

The project includes `src.subtitle_qa` and the `video-subtitle-qa` entry point for subtitle diagnostics. The repair layer handles missing/invalid historical VTT artifacts.

Recovery rules:

1. invalid/missing original VTT → rerun STT, validate, then translate;
2. valid original + invalid/missing translation → keep original timing and rerun translation;
3. both invalid → rerun STT once, validate, then translate.

Existing VTT files are backed up before replacement. A valid VTT is not unnecessarily regenerated.

## Output conventions

The output may contain an original transcription under `original_transcriptions/` and a translated VTT named according to the configured target language. Do not hard-code a language suffix in operational tooling; inspect the generated output or configuration.
