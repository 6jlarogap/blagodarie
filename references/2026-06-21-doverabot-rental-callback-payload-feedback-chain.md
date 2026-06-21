# Doverabot Rental Callback Payload Feedback Chain

Date: 2026-06-21
Status: implemented
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

Pending operational handoff:

- commit with message `doverabot-rental-callback-payload-feedback`;
- deploy bot/runtime code through the wrapper;
- record deploy/status/log results.

## Follow-Up Basket

- Centralize remaining legacy callback parsing outside rental.
- Fix duplicate callback function names in older handlers.
- Replace remaining hard-coded bot/deep links where they are not already derived from `bot_data.username` or settings.
- Continue improving unauthorized/expired callback feedback across non-rental flows.
