# Doverabot Rental Durable FSM Hermes Map Marker Tests Chain

Date: 2026-06-21
Status: implemented, source checks run
Started `/new-go-slug`: `doverabot-rental-durable-fsm-hermes-map-marker-tests`
Parent chain: [2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md](2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md)

## Scope

Close the hardening basket for the rental runtime flow:

- replace volatile bot FSM storage with durable storage;
- lock the rental voice-search STT handoff as an explicit Organizm/Hermes contract;
- make rental map points visible and visually distinct in the deployed map path;
- add mocked aiogram-level tests for rental callbacks, command interruption, voice STT payloads, and map links.

## Implemented

- Added Redis-backed aiogram FSM storage selection in `telegram-bot/main.py`, using `BOT_FSM_STORAGE=redis` by default and a memory override for local-only development.
- Added bot settings for the named `organizm_hermes_v1` rental STT contract, language, and Redis FSM configuration.
- Split rental STT request/response handling into testable helpers:
  - JSON `file_id` payload is the default Hermes handoff;
  - multipart `download` mode remains supported through settings.
- Added `Show on map` rental inline button when an offer has coordinates.
- Added rental map UUID targeting, a dedicated rental marker SVG data URL, marker metadata, and owner icon preservation in `/api/user/points/`.
- Added a small deployed-map wrapper in `frontend/map_npm/dist/index.html` so `?rental=on` and rental filter params are forwarded to `/api/user/points/` without rebuilding the missing map source bundle.
- Added mocked bot tests in `telegram-bot/tests/test_handler_rental.py`.
- Added backend map point tests for marker payload, UUID targeting, filters, and invalid UUID handling.

## Verification

Passed:

- `python3 -m py_compile app/users/views.py app/users/tests.py telegram-bot/main.py telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m unittest discover telegram-bot/tests`
- `/srv/blagodarie/venv-app/bin/python manage.py check`
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations --check --dry-run` -> no changes detected; emitted the known local PostgreSQL socket warning while checking migration history.
- `python3 -m compileall telegram-bot`
- `uv tool run --from graphifyy graphify update .`

Blocked:

- `/srv/blagodarie/venv-app/bin/python manage.py test users`

Reason: local PostgreSQL peer authentication rejects the current OS user for database user `postgres` while creating the test database:

`django.db.utils.OperationalError: connection failed: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL: Peer authentication failed for user "postgres"`

## Operational Handoff

Pending source commit and deployment wrapper checks.
