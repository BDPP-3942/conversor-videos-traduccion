#!/usr/bin/env bash

# Resolve the uv executable used by project wrappers.
# Project-managed uv takes precedence so a source checkout is reproducible even
# when no global uv installation is present.
resolve_uv() {
    local project_dir="${1:?project directory required}"
    local local_uv="$project_dir/tools/uv/uv"

    if [[ -x "$local_uv" ]]; then
        printf '%s\n' "$local_uv"
        return 0
    fi

    if command -v uv >/dev/null 2>&1; then
        command -v uv
        return 0
    fi

    return 1
}
