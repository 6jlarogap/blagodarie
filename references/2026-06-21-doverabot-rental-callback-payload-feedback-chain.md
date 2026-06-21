# Doverabot Rental Callback Payload Feedback Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-rental-callback-payload-feedback`
Parent chain: [doverabot-rental-offers-chain.md](doverabot-rental-offers-chain.md)

## Scope

Close the next narrow rental hardening item from the architecture backlog:

- centralize rental booking/contact/reservation callback payload parsing;
- reject stale or malformed rental callback payloads before they hit API calls or FSM state;
- show user-visible feedback for stale callback buttons and profile-auth failures;
- keep the change limited to the rental bot surface.

## Implemented

- Added rental-specific callback parsing helpers in `telegram-bot/handler_rental.py`.
- Validated supported reservation actions and numeric reservation ids before changing state or calling the backend.
- Replaced silent `callback.answer()` exits for malformed/auth-failed rental callbacks with alert text.
- Added mocked bot tests for stale booking callbacks, invalid reservation action callbacks, malformed reservation ids, and contact auth failure.

## Verification

Passed:

- `python3 -m py_compile telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m unittest discover telegram-bot/tests`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/`
- `uv tool run --from graphifyy graphify update .`

## Operational Handoff

Source commit:

- `git commit -m "doverabot-rental-callback-payload-feedback"` -> `ee651ce`

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

- Centralize remaining legacy callback parsing outside rental.
- Fix duplicate callback function names in older handlers.
- Replace remaining hard-coded bot/deep links where they are not already derived from `bot_data.username` or settings.
- Continue improving unauthorized/expired callback feedback across non-rental flows.
