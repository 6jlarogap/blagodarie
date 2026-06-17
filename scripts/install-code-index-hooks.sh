#!/usr/bin/env bash
# Configure this checkout to rebuild CODE_INDEX.md through repo-local Git hooks.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

git config core.hooksPath .githooks
bash scripts/reindex.sh
