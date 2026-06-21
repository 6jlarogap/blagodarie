# Doverabot Legacy Relatives Media Command Tests Chain

Date: 2026-06-21
Status: implemented and deployed
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

Source commit:

- `git commit -m "doverabot-legacy-relatives-media-command-tests"` -> `54bdbbd`

Deploy checks:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with pre-existing `security.W002` clickjacking middleware warning.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx, web, and bot active before deploy.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply; same pre-existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test passed and web/bot restarted.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 60` -> recent Jun 21 web restart, no new traceback in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 80` -> recent Jun 21 bot restart, no new traceback in the checked tail.

## Follow-Up Basket

- Continue replacing remaining hard-coded bot links where `bot_data.username` or settings can provide the runtime value.
- Consider a later, separate profile-edit cleanup for remaining non-media direct callback splits in `handler_callbacks.py`.
