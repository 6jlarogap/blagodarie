#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)

cd "$REPO_ROOT"

if [ "$(id -u)" -eq 0 ]; then
  exec bash deploy/install-blagodarie-admin-workflow.sh
fi

exec sudo bash deploy/install-blagodarie-admin-workflow.sh
