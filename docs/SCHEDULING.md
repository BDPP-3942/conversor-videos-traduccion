# Scheduling and unattended execution

The application separates interactive administration from unattended processing.

## Scheduled command

```bash
python main.py run --scheduled
```

Scheduled mode uses the saved active provider configuration and does not open a browser or request interactive input.

## Supported scheduler integrations

Repository scripts provide support for:

- Windows Task Scheduler (`scripts/install_task_scheduler.ps1`);
- macOS `launchd` (`scripts/install_launchd.sh`);
- cron-style execution on Linux/macOS;
- unattended wrapper scripts under `scripts/run_unattended.*` and `scripts/run_scheduled.*`.

A scheduled process must have a deterministic working directory, access to configuration/secrets/models, write permissions for runtime state and logs, and the intended Python environment or packaged executable.

## Cloud authentication

Google Drive uses persistent OAuth credentials and silent refresh where possible. rclone manages OAuth credentials for its remotes. Scheduled execution never performs interactive consent; a credential requiring reauthorization causes readiness to fail instead.

## Concurrency

The pipeline uses a runtime lock. Do not configure multiple independent scheduler tasks to process the same runtime directory concurrently.
