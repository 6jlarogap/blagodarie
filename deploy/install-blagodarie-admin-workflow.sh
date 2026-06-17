#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash deploy/install-blagodarie-admin-workflow.sh" >&2
  exit 1
fi

MAINT_USER=vdrzd
MAINT_GROUP=doverabot-maint

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
ADMIN_SRC="$REPO_ROOT/deploy/bin/blagodarie-admin"

if [ ! -f "$ADMIN_SRC" ]; then
  echo "Missing admin wrapper source: $ADMIN_SRC" >&2
  exit 1
fi

groupadd --force "$MAINT_GROUP"
usermod -aG "$MAINT_GROUP" "$MAINT_USER"

install -o root -g root -m 0755 "$ADMIN_SRC" /usr/local/sbin/blagodarie-admin

cat > /etc/sudoers.d/blagodarie-admin <<SUDOERS
$MAINT_USER ALL=(root) NOPASSWD: /usr/local/sbin/blagodarie-admin *
SUDOERS
chown root:root /etc/sudoers.d/blagodarie-admin
chmod 0440 /etc/sudoers.d/blagodarie-admin
visudo -cf /etc/sudoers.d/blagodarie-admin

echo "Installed /usr/local/sbin/blagodarie-admin"
echo "Try: sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run"
