#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: sudo bash scripts/enable-agent-deploy-permissions.sh

Installs the narrow blagodarie-admin sudo wrapper and verifies that the
maintenance user can run it non-interactively. This is the permission surface
Codex needs for deployment:

  sudo -n /usr/local/sbin/blagodarie-admin COMMAND

The script does not grant broad sudo. It delegates installation to
deploy/install-blagodarie-admin-workflow.sh, which permits only
/usr/local/sbin/blagodarie-admin * for the maintenance user.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root:" >&2
  echo "  sudo bash scripts/enable-agent-deploy-permissions.sh" >&2
  exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
INSTALLER="$REPO_ROOT/deploy/install-blagodarie-admin-workflow.sh"
MAINT_USER=vdrzd
ADMIN=/usr/local/sbin/blagodarie-admin
SUDOERS=/etc/sudoers.d/blagodarie-admin

if [[ ! -f "$INSTALLER" ]]; then
  echo "Missing installer: $INSTALLER" >&2
  exit 1
fi

echo "Installing blagodarie-admin wrapper..."
bash "$INSTALLER"

echo "Verifying sudoers syntax..."
visudo -cf "$SUDOERS"

dry_run_output=$(mktemp)
cleanup() {
  rm -f "$dry_run_output"
}
trap cleanup EXIT

echo "Verifying noninteractive deploy dry-run for $MAINT_USER..."
sudo -n -u "$MAINT_USER" sudo -n "$ADMIN" deploy-dry-run >"$dry_run_output"
if grep -q 'scripts/unblock-django-test-db.sh' "$dry_run_output"; then
  echo "Dry-run still includes scripts/unblock-django-test-db.sh; wrapper exclusion is not active." >&2
  exit 1
fi

echo "Agent deploy permissions are ready."
echo "Codex can now run: sudo -n $ADMIN deploy-dry-run"
