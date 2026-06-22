# Doverabot Rental Medium STT Adapter Chain

Date: 2026-06-22
Slug: `doverabot-rental-medium-stt-adapter`
Status: port change in progress
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)

## Queue

1. `doverabot-rental-medium-stt-adapter`

## Scope

- Add a Doverabot-owned localhost HTTP STT adapter for rental voice messages.
- Use faster-whisper `medium` with Russian defaults and the existing
  `organizm_hermes_v1` bot STT contract.
- Keep the adapter bound to `127.0.0.1:8766` and require multipart
  `voice`, `contract`, and optional `language`.
- Configure live bot runtime settings for the localhost adapter:
  `RENTAL_STT_URL=http://127.0.0.1:8766/transcribe`,
  `RENTAL_STT_MODE=download`, and `RENTAL_STT_LANGUAGE=ru`.
- Extend the admin wrapper with rental STT install, restart, status, and log
  commands.

## Out Of Scope

- Reusing the organism Telegram bridge directly.
- Backend model/API migrations.
- Public network exposure or token auth for the STT adapter.

## Stop Rule

If STT venv install, systemd install, bot runtime setting, bot restart, or
health/log checks are blocked, record the exact failed command and do not mark
the chain deployed.

## Implementation Plan

- Add `telegram-bot/rental_stt_adapter.py`.
- Add `pip-rental-stt.txt` with `aiohttp` and `faster-whisper`.
- Keep the existing safe `bot-runtime-setting` admin-wrapper changes and add
  service management for `doverabot-rental-stt.service`.
- Run the requested source checks and `graphify update .`.
- Commit with message `doverabot-rental-medium-stt-adapter`.
- Install/update wrapper, install the STT service/venv, set runtime settings,
  restart STT and bot, and verify health/status/logs.

## Verification

- `bash -n deploy/bin/blagodarie-admin` -> OK.
- `python3 -m py_compile telegram-bot/rental_stt_adapter.py` -> OK.
- `python3 -m unittest discover telegram-bot/tests -p 'test_handler_rental.py'`
  -> 39 tests OK; the existing mocked geocoding failure path logged the
  expected `RuntimeError: lookup failed`.
- `python3 -m compileall telegram-bot` -> OK.
- `git diff --check` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK.

Source commit:

- `321ee4e` `doverabot-rental-medium-stt-adapter`

## Operational Handoff

Runtime deployment is blocked by an existing listener on the required localhost
port:

- The maintainer manually ran `sudo bash deploy/install-blagodarie-admin-workflow.sh`
  after the initial sudo-auth blocker; the updated wrapper installed
  successfully.
- `sudo -n /usr/local/sbin/blagodarie-admin install-rental-stt` -> installed
  the venv dependencies, wrote/enabled the systemd unit, and attempted to start
  `doverabot-rental-stt.service`.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-rental-stt 80` -> the adapter
  fails on startup with `OSError: [Errno 98] error while attempting to bind on
  address ('127.0.0.1', 8765): [errno 98] address already in use`.
- `curl --noproxy '*' -fsS http://127.0.0.1:8765/healthz` -> returned
  `{"object": "list", "data": [{"id": "claude-sonnet-4-6"}]}`, which is not
  the adapter health response and confirms the port is occupied by another
  service.
- `sudo -n ss -ltnp 'sport = :8765'` -> blocked by sudoers with
  `sudo: interactive authentication is required`, so the owning PID was not
  identifiable from this session.
- `sudo -n systemctl stop doverabot-rental-stt.service` -> stopped the failing
  restart loop.
- `sudo -n /usr/local/sbin/blagodarie-admin status-rental-stt` -> inactive
  (dead), last exit status 1 from the bind failure.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot
  are active; rental STT is inactive.
- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting status all` ->
  `RENTAL_STT_URL=missing`, `RENTAL_STT_TOKEN=missing`,
  `RENTAL_STT_MODE=missing`, `RENTAL_STT_CONTRACT=missing`,
  `RENTAL_STT_LANGUAGE=missing`.

Per the stop rule, live bot STT runtime settings were not changed, the bot was
not restarted, and this chain is not marked deployed.
