# Blagodarie Maintenance Workspace

This directory is the editable source workspace for the live deployment at
`/srv/blagodarie`.

Secrets and runtime state are intentionally excluded from this workspace:

- `app/app/local_settings.py`
- `telegram-bot/settings_local.py`
- `telegram-bot-api/`
- `venv-app/`
- `app/media/`
- `audit/`
- temp/cache directories

After editing source here, deploy with the root-owned wrapper:

```bash
sudo -n /usr/local/sbin/blagodarie-admin deploy
```

If the wrapper is missing, install it once from the host account:

```bash
sudo bash /home/vdrzd/doverabot-repair/admin-install-blagodarie-workflow.sh
```

Useful checks:

```bash
sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run
sudo -n /usr/local/sbin/blagodarie-admin check-django
sudo -n /usr/local/sbin/blagodarie-admin is-active
sudo -n /usr/local/sbin/blagodarie-admin logs-web 120
sudo -n /usr/local/sbin/blagodarie-admin logs-bot 120
```
