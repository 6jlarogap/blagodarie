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

Useful checks:

```bash
sudo -n /usr/local/sbin/blagodarie-admin check-django
sudo -n /usr/local/sbin/blagodarie-admin is-active
sudo -n /usr/local/sbin/blagodarie-admin logs-web 120
sudo -n /usr/local/sbin/blagodarie-admin logs-bot 120
```
