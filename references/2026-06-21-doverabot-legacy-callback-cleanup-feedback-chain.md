# Doverabot Legacy Callback Cleanup Feedback Chain

Date: 2026-06-21
Status: source implemented, deploy pending
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

Pending source commit and runtime deploy.
