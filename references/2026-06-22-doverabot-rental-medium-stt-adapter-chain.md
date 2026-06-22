# Doverabot Rental Medium STT Adapter Chain

Date: 2026-06-22
Slug: `doverabot-rental-medium-stt-adapter`
Status: implemented and deployed
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
- After the `8765` conflict, `curl --noproxy '*' -fsS
  http://127.0.0.1:8766/healthz` before the port change -> connection refused,
  confirming the replacement port was free.
- Port-change checks:
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
- `4bd1ce6` `doverabot-rental-medium-stt-adapter port`

## Operational Handoff

The original `127.0.0.1:8765` target was occupied by another localhost service,
so the adapter and live bot runtime setting were moved to `127.0.0.1:8766`.

Deploy checks:

- The maintainer manually ran `sudo bash deploy/install-blagodarie-admin-workflow.sh`
  after the initial sudo-auth blocker; the updated wrapper installed
  successfully.
- `sudo -n /usr/local/sbin/blagodarie-admin install-rental-stt` -> installed
  the venv dependencies, wrote/enabled the systemd unit, and verified the
  service command path. The first start exposed the `8765` bind conflict.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy-rental-stt` -> synced the
  `8766` source change and restarted `doverabot-rental-stt.service`.
- `curl --noproxy '*' -fsS http://127.0.0.1:8766/healthz` -> returned
  `{"ok": true, "contract": "organizm_hermes_v1", "language": "ru",
  "loaded": false, "max_file_size": 26214400, "model": "medium"}`.
- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting set
  RENTAL_STT_URL http://127.0.0.1:8766/transcribe` -> set.
- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting set
  RENTAL_STT_MODE download` -> set.
- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting set
  RENTAL_STT_LANGUAGE ru` -> set.
- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting set
  RENTAL_STT_CONTRACT organizm_hermes_v1` -> set.
- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting status all` ->
  `RENTAL_STT_URL=set`, `RENTAL_STT_TOKEN=missing`, `RENTAL_STT_MODE=set`,
  `RENTAL_STT_CONTRACT=set`, `RENTAL_STT_LANGUAGE=set`.
- `sudo -n /usr/local/sbin/blagodarie-admin restart-rental-stt` -> completed.
- `sudo -n /usr/local/sbin/blagodarie-admin restart-bot` -> completed.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, bot, and
  rental STT all active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-rental-stt 80` -> shows the
  new process running on `http://127.0.0.1:8766` and successful `/healthz`
  requests; earlier `8765` bind errors remain in history.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 80` -> shows the bot
  restart completed; no new STT-related error was present in the checked tail.

No migrations were added or required.
