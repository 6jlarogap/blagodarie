# Doverabot Profile Edit State Feedback Finish Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-profile-edit-state-feedback-finish`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Prior hardening chain: [2026-06-21-doverabot-profile-edit-callback-feedback-finish-chain.md](2026-06-21-doverabot-profile-edit-callback-feedback-finish-chain.md)

## Scope

Finish the profile-edit message-state feedback slice in `telegram-bot/handler_callbacks.py`:

- replace silent state clears or returns in profile-edit message handlers with visible user feedback for stale FSM data, profile auth failure, and API failure;
- preserve successful IOF, meet onboarding, date, comment, message, user description, banking, and thank-bank media-pack flows;
- keep command interruption behavior routed through the existing `is_it_command` cancellation path;
- add mocked handler coverage for invalid state, auth failure, API failure, and command interruption.

## Implemented

- Added local message-state feedback helpers for stale profile-edit FSM state and Redis media-pack timeout paths.
- Added visible prompts to previously silent profile edit message handlers for IOF, meet DOB/description, banking after invite, date/date-of-death, comments, send-message, user description, banking, and thank-bank message states.
- Kept multi-message media-pack semantics intact: non-first media items still return quietly, while Redis timeout/stale-state paths now tell the user before clearing state.
- Added mocked regression tests for stale DOB state, comment auth failure, send-message API exception, user-desc auth failure, and profile IOF command interruption.

## Verification

Passed before source commit:

- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_callbacks.py telegram-bot/handler_relatives.py telegram-bot/handler_bot.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 46 tests OK.
- `python3 -m unittest discover telegram-bot/tests` -> 46 tests OK.
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> no issues.
- `git diff --check`
- `uv tool run --from graphifyy graphify update .` -> rebuilt code graph.

## Operational Handoff

Source commit:

- `git commit -m "doverabot-profile-edit-state-feedback-finish"` -> `bacb27a`

Deploy checks:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with pre-existing `security.W002` clickjacking middleware warning.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx, web, and bot active before deploy.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply; same pre-existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test passed and web/bot restarted.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 30` -> recent Jun 21 web restart, no new failure lines in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 30` -> recent Jun 21 bot restart, no new failure lines in the checked tail.

## Follow-Up Basket

- No immediate follow-up `/new-go-slug` was selected in this slice.
- Keep future Doverabot hardening scoped to the remaining general backlog: callback/parser cleanup, handler coverage, duplicate handler names, and bot/deep-link consistency in newly touched flows.
