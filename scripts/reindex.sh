#!/usr/bin/env bash
# Rebuild CODE_INDEX.md using the repo-local code-index generator.
set -euo pipefail

ROOT="${CODE_INDEX_ROOT:-}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

CODE_INDEX_ROOT="$ROOT" python3 "$ROOT/scripts/code_index.py" "$@"
