#!/usr/bin/env bash
# Soft Codex hook: keep CODE_INDEX.md visible before shell-based code work.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if [[ ! -f CODE_INDEX.md ]]; then
  echo "[code-index] CODE_INDEX.md is missing; run: bash scripts/reindex.sh" >&2
  exit 0
fi

stale_file="$(
  find . \
    \( -type d \
       \( -name '.cache' -o -name '.git' -o -name '.mypy_cache' -o -name '.pytest_cache' \
          -o -name '.ruff_cache' -o -name '.tox' -o -name '.venv' -o -name '__pycache__' \
          -o -name 'build' -o -name 'dist' -o -name 'ENV' -o -name 'graphify-out' \
          -o -name 'media' -o -name 'migrations' -o -name 'node_modules' \
          -o -name 'telegram-bot-api' -o -name 'tmp' -o -name 'venv' -o -name 'venv-app' \
          -o -name 'venv-rental-stt' \) \
       -o -path './app/static' -o -path './audit' \
       -o -path './frontend/graph_npm/dist' -o -path './frontend/map_npm/dist' \
       -o -path './frontend/mgraph/dist' \) -prune \
    -o -type f \
    \( -name '*.py' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.java' -o -name '*.md' -o -name '*.sh' \) \
    ! -name 'CODE_INDEX.md' ! -name '*.min.js' -newer CODE_INDEX.md -print -quit \
    2>/dev/null || true
)"

if [[ -n "$stale_file" ]]; then
  echo "[code-index] CODE_INDEX.md may be stale; newer indexed file: ${stale_file#./}. Run: bash scripts/reindex.sh" >&2
fi

stamp="${TMPDIR:-/tmp}/code-index-hook-${ROOT//\//_}.stamp"
if [[ ! -f "$stamp" ]]; then
  echo "[code-index] For codebase work, use graphify for relationships and CODE_INDEX.md/nearest subindex for exact source reads." >&2
  : > "$stamp" 2>/dev/null || true
fi

exit 0
