# Mobile feasibility

## Decision

**VIABLE CON CAMBIOS.** The current project is strongly local-first and has no mobile-facing backend/job API. The heavy stages—Whisper, CTranslate2 translation, TTS and FFmpeg—are better treated as backend workloads for a mobile product rather than assumed to run on every phone.

## Recommended architecture

```text
Mobile iOS/Android
        |
     HTTPS API
        |
   Authentication
        |
     Job API
        |
   Queue / workers
        |
 +------+-------+--------+
 |      |       |        |
 STT translation TTS   FFmpeg
        |
   Object storage
```

The existing pipeline and storage/provider abstractions are useful backend building blocks. A future API should call application/use cases rather than invoke CLI parsers or duplicate `MediaPipeline` logic.

## Mobile responsibilities

- authentication and secure token storage;
- select/upload videos or ZIPs;
- configure source/target language and processing options;
- create and monitor jobs;
- display progress and recoverable errors;
- download/share completed artifacts;
- work correctly when the app is backgrounded or temporarily offline.

## Backend responsibilities

- STT and selective recovery;
- translation providers and fallback policy;
- local translation models where economical;
- TTS and media synchronization;
- FFmpeg processing;
- durable job state, retries and idempotency;
- object storage and lifecycle cleanup;
- authorization, quotas and abuse controls.

## API shape to evaluate

A future implementation will likely need asynchronous job resources rather than an HTTP request held open for the duration of video processing. Candidate operations are creation, status/progress, cancellation, and result retrieval; exact routes should be defined after the backend storage and authentication model are selected.

## Costs and risks

No cloud cost is asserted from the repository alone. The main variables to benchmark are video duration, source bitrate, STT model/device, translation provider and volume, TTS duration, FFmpeg CPU/GPU time, object-storage retention and egress. These measurements should drive the choice between managed APIs and self-hosted workers.

Security requirements include authenticated jobs, per-user authorization, upload-size/type validation, isolated temporary workspaces, rate limits, signed result URLs where appropriate, deletion/retention policies and never exposing provider credentials to the mobile client.

The mobile product should therefore be treated as a new backend-backed architecture rather than a thin mobile wrapper around the current local executable.
