# Doverabot Legacy Callback Cleanup Feedback Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-legacy-callback-cleanup-feedback`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Prior callback chain: [2026-06-21-doverabot-rental-callback-payload-feedback-chain.md](2026-06-21-doverabot-rental-callback-payload-feedback-chain.md)

## Scope

Continue bot hardening outside the rental callback path:

- centralize remaining mixed legacy callback payload parsing helpers;
- clean up duplicate legacy callback handler names;
- add user-visible feedback for malformed, stale, or unauthorized non-rental callbacks;
- keep the change limited to bot callback code and mocked bot tests.

## Implemented

- Added shared `Misc` callback parsing helpers and alert feedback helpers in `telegram-bot/common.py`.
- Routed legacy offer, donate-thank, meet-edit, location, attitude, and sympathy invalid/auth callback exits through visible callback alerts.
- Centralized offer callback parsers on `Offer` for answer, donation choice, and donation revoke payloads.
- Renamed duplicate callback coroutine names:
  - `cbq_gender` -> `cbq_gender_from_card` and `cbq_gender_from_state`;
  - `cbq_donate_office_choice` -> `cbq_donate_offer_choice` and `cbq_donate_offer_revoke_choice`.
- Added mocked bot tests for shared callback parsing, stale-button alerts, and offer auth failure alerts.

## Verification

Passed before source commit:

- `python3 -m unittest discover telegram-bot/tests`
- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_callbacks.py telegram-bot/handler_sympas.py telegram-bot/handler_offer.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/`
- `uv tool run --from graphifyy graphify update .`

## Operational Handoff

Source commit:

- `git commit -m "doverabot-legacy-callback-cleanup-feedback"` -> `2ebc3b3`

Deploy checks:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with pre-existing `security.W002` clickjacking middleware warning.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx, web, and bot active before deploy.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply; same pre-existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test passed and web/bot restarted.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot active.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'` -> HTTP 200, `{"offers":[]}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/user/points/?rental=on'` -> HTTP 200, empty points payload.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 40` -> recent Jun 21 web restart, no new traceback in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 40` -> recent Jun 21 bot restart, no new traceback in the checked tail.

## Follow-Up Basket

- Continue converting remaining direct legacy callback splits in relatives/profile media flows.
- Add handler tests around relatives, media packs, and command interruption outside rental.
- Replace remaining hard-coded bot links where `bot_data.username` or settings can provide the runtime value.

Suggested next `/new-go-slug`: `doverabot-legacy-relatives-media-command-tests`.
