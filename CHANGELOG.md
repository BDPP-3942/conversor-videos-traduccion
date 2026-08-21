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
