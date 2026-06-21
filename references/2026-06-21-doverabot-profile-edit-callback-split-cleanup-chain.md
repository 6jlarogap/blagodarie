# Doverabot Profile Edit Callback Split Cleanup Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-profile-edit-callback-split-cleanup`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Prior hardening chain: [2026-06-21-doverabot-runtime-bot-link-cleanup-chain.md](2026-06-21-doverabot-runtime-bot-link-cleanup-chain.md)

## Scope

Continue legacy Doverabot hardening outside the rental path:

- clean up remaining direct `callback.data.split(KeyboardType.SEP)` use in profile-edit callback flows;
- route malformed/stale or unauthorized profile-edit callback exits through shared visible notices where those paths were touched;
- keep successful profile edit, meet edit, attitude, and date flows unchanged;
- add mocked handler coverage for the edited callback failure paths.

## Implemented

- Replaced remaining direct callback data splits in `telegram-bot/handler_callbacks.py` with shared `Misc` parser helpers.
- Covered new-person gender, profile gender, meet gender, attitude, and date-of-death status callback parsing.
- Fixed the meet gender callback auth guard so it no longer references FSM `data` before loading it.
- Added visible stale/auth callback alerts for malformed or unauthorized branches in the edited profile-edit callbacks.
- Added mocked bot tests for malformed new-person gender, profile gender, attitude, and DOD callbacks, plus profile/meet gender auth failures.

## Verification

Passed before source commit:

- `python3 -m unittest discover telegram-bot/tests` -> 29 tests OK.
- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_callbacks.py telegram-bot/handler_relatives.py telegram-bot/handler_bot.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> no issues.
- `rg -n "callback\\.data\\.split|\\.data\\.split\\(KeyboardType\\.SEP\\)" telegram-bot/handler_callbacks.py` -> no matches.
- `uv tool run --from graphifyy graphify update .`

## Operational Handoff

Source commit:

- `git commit -m "doverabot-profile-edit-callback-split-cleanup"` -> `ab6dfdf`

Deploy checks:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK; showed expected bot source deltas.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with pre-existing `security.W002` clickjacking middleware warning.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx, web, and bot active before deploy.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply; same pre-existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test passed and web/bot restarted.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 60` -> recent Jun 21 web restart, no new traceback in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 80` -> recent Jun 21 bot restart, no new traceback in the checked tail.

## Follow-Up Basket

- Continue profile-edit callback cleanup for remaining parser-backed but silent stale/auth exits in `handler_callbacks.py`: IOF, DOB unknown, comment, delete/undelete, send-message/archive, user description, and banking.
- Keep the next slice limited to visible callback feedback and mocked handler coverage.

Suggested next `/new-go-slug`: `doverabot-profile-edit-callback-feedback-finish`.
