# Doverabot Rental Medium STT Adapter Chain

Date: 2026-06-22
Slug: `doverabot-rental-medium-stt-adapter`
Status: source implemented, runtime blocked
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)

## Queue

1. `doverabot-rental-medium-stt-adapter`

## Scope

- Add a Doverabot-owned localhost HTTP STT adapter for rental voice messages.
- Use faster-whisper `medium` with Russian defaults and the existing
  `organizm_hermes_v1` bot STT contract.
- Keep the adapter bound to `127.0.0.1:8765` and require multipart
  `voice`, `contract`, and optional `language`.
- Configure live bot runtime settings for the localhost adapter:
  `RENTAL_STT_URL=http://127.0.0.1:8765/transcribe`,
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

Runtime deployment is blocked. The updated wrapper source is committed, but the
live `/usr/local/sbin/blagodarie-admin` wrapper cannot be updated without sudo
authentication:

- `sudo bash deploy/install-blagodarie-admin-workflow.sh` -> failed:
  `sudo: A terminal is required to authenticate`.
- `sudo -n /usr/local/sbin/blagodarie-admin install-rental-stt` -> failed with
  exit 2 because the currently installed wrapper does not yet include the new
  `install-rental-stt` command.

Current live state checked before stopping:

- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting status all` ->
  `RENTAL_STT_URL=missing`, `RENTAL_STT_TOKEN=missing`,
  `RENTAL_STT_MODE=missing`, `RENTAL_STT_CONTRACT=missing`,
  `RENTAL_STT_LANGUAGE=missing`.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot
  are active.

Per the stop rule, the STT venv/service install, health check, runtime setting
changes, STT restart, bot restart, and STT log checks were not run, and this
chain is not marked deployed.
