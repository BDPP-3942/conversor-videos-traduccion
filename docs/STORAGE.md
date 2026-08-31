# Storage

The processing pipeline uses a storage abstraction so processing logic is shared across backends.

## Supported backends

- `local`
- `google_drive` / `gdrive`
- `rclone`

The provider must use matching URI schemes for source and target. Local defaults are `local://storage/input` and `local://storage/output`.

## Local layout

```text
storage/
├── input/
├── work/
├── output/
│   └── _manifests/
├── archive/
├── failures/
├── logs/
└── state/
```

The application also uses `secrets/` for credentials/profiles and `tools/` for managed/external runtime resources.

## Cloud processing

Cloud-backed runs use the same common pipeline. Inputs are accessed through the selected adapter and outputs are validated before completion/archival actions. Cloud authentication must be prepared before scheduled execution.

Do not delete local output merely because an upload was initiated; the transfer must be confirmed.
