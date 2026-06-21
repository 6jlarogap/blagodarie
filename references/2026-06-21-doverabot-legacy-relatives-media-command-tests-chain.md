# Doverabot Legacy Relatives Media Command Tests Chain

Date: 2026-06-21
Status: source verified; operational handoff pending
Started `/new-go-slug`: `doverabot-legacy-relatives-media-command-tests`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Prior callback chain: [2026-06-21-doverabot-legacy-callback-cleanup-feedback-chain.md](2026-06-21-doverabot-legacy-callback-cleanup-feedback-chain.md)

## Scope

Continue legacy Doverabot hardening outside the rental path:

- convert relatives and profile-photo callback failure exits to shared visible callback notices;
- keep existing successful relatives/photo flows unchanged;
- add mocked handler coverage for relatives callbacks, profile media callbacks, media pack extraction, and non-rental command interruption.

## Implemented

- Routed malformed relatives callback payloads through `Misc.answer_callback_notice`.
- Routed relatives ownership/auth failures through the shared profile/auth callback alert.
- Replaced remaining direct `callback.data.split(KeyboardType.SEP)` use in the edited relatives branches with shared callback helpers.
- Routed malformed and unauthorized profile-photo callbacks through shared stale/auth alerts.
- Fixed local profile-photo error paths that could reference undefined `msg_error` or `message` names.
- Extended mocked aiogram test stubs enough to import real profile callback code.
- Added tests for relatives callback feedback, profile-photo callback feedback, `TgDesc.from_message` media pack extraction, and non-rental command interruption in a relatives FSM handler.

## Verification

Passed before source commit:

- `python3 -m unittest discover telegram-bot/tests` -> 22 tests OK.
- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_callbacks.py telegram-bot/handler_relatives.py telegram-bot/handler_bot.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> no issues.
- `uv tool run --from graphifyy graphify update .`

## Operational Handoff

Pending source commit and runtime deploy.
