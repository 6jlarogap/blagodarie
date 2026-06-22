# Doverabot Rental Medium STT Adapter Chain

Date: 2026-06-22
Slug: `doverabot-rental-medium-stt-adapter`
Status: planned
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

Pending.

## Operational Handoff

Pending.
