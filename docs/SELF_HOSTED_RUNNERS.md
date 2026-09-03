# Self-hosted GitHub Actions runners

This project uses the private development tower for Windows and Linux CI, while macOS remains GitHub-hosted.

## Required topology

| Runner | Host | Labels | Role |
|---|---|---|---|
| Windows | Native Windows x64 | `self-hosted`, `windows`, `x64` | Windows/Python 3.11-3.13 compatibility |
| Linux | WSL2 Ubuntu x64 | `self-hosted`, `linux`, `x64` | Linux/Python 3.11-3.13, quality, packaging and audits |
| macOS | GitHub-hosted | `macos-latest` | macOS/Python 3.11-3.13 compatibility |

The Windows and Linux runners are separate GitHub runner installations. They may live on the same physical tower, but they share its CPU, memory, storage and network resources.

## Windows runner prerequisites

- Windows x64 host.
- Git installed and available to the runner service.
- Python 3.11, 3.12 and 3.13 available through the runner's tool cache or installable by `actions/setup-python`.
- PowerShell available.
- `cmd.exe` available.
- Network access for Python package installation and GitHub Actions.
- FFmpeg available if the integration/E2E tests require it on this runner.

Register the runner from the repository's GitHub Settings > Actions > Runners page and apply the labels `windows` and `x64` in addition to the automatically supplied `self-hosted` label.

## WSL2 Linux runner prerequisites

- WSL2 with an Ubuntu distribution.
- x64 Linux userspace.
- Git and Bash.
- Python 3.11, 3.12 and 3.13 available through the runner's tool cache or installable by `actions/setup-python`.
- Network access for Python package installation and GitHub Actions.
- FFmpeg available if the integration/E2E tests require it on this runner.

Install a separate GitHub Actions runner inside the WSL2 Ubuntu environment. Apply the labels `linux` and `x64` in addition to `self-hosted`.

## Concurrency expectations

The workflow deliberately uses a single runner label set for Windows and one for Linux. If only one physical runner matches a label set, the three Python matrix jobs execute sequentially on that runner. This is intentional: adding multiple runner registrations to the same physical machine does not create additional CPU/RAM capacity.

If later needed, additional physical machines can be added with the same labels and GitHub will distribute eligible jobs among them.

## Security and maintenance

A self-hosted runner executes workflow code from the repository. Do not register a self-hosted runner against repositories whose contributors cannot be trusted with code execution on the machine. Keep the runner account and operating system patched, and avoid storing long-lived secrets or unrelated personal data on the runner host.

The runner should be dedicated to CI workloads as far as practical. For GPU workloads, use separate labels and concurrency controls rather than allowing normal matrix tests to compete with AI/video processing.
