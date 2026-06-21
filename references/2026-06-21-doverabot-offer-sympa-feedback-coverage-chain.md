# Doverabot Offer Sympa Feedback Coverage Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-offer-sympa-feedback-coverage`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)

## Scope

Add mocked coverage and visible feedback around legacy offer and sympathy
failure paths:

- stale/missing-state, auth, and API failure exits in `telegram-bot/handler_offer.py`;
- stale/auth/API exits in sympathy donation and callback paths in
  `telegram-bot/handler_sympas.py`;
- command interruption while the bot waits for offer donation or sympathy
  donation media/text;
- unchanged successful offer message delivery and sympathy contact behavior.

## Implemented

- Added offer-side visible replies for stale FSM data, profile auth failure,
  and API failure in offer geo, description/location editing, offer broadcast,
  and offer-donation message states.
- Added callback alerts for stale/auth/API exits in offer geo pass, offer
  description lookup, malformed/auth donation choices, and offer donation
  revoke/choice branches already covered by parser guards.
- Added sympathy-side visible replies for stale/auth/API exits in the
  reciprocal-sympathy donation message state, plus command interruption via
  `is_it_command`.
- Added sympathy callback alerts for donation prompt API failure and
  hide/show/mistrust/revoke API failure exits while preserving the existing
  `already` mistrust success path.
- Extended mocked bot tests with offer/sympathy feedback coverage and a
  successful offer participant-message delivery regression.

## Verification

Passed before source commit:

- `python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 61 tests OK.
- `python3 -m unittest discover telegram-bot/tests` -> 61 tests OK.
- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_callbacks.py telegram-bot/handler_relatives.py telegram-bot/handler_bot.py telegram-bot/handler_offer.py telegram-bot/handler_sympas.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> no issues.
- `git diff --check`
- `uv tool run --from graphifyy graphify update .` -> rebuilt code graph.

## Operational Handoff

Source commit:

- `git commit -m "doverabot-offer-sympa-feedback-coverage"` -> `8024078`

Deploy checks:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with
  pre-existing `security.W002` clickjacking middleware warning.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx, web, and bot
  active before deploy.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply;
  same pre-existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test
  passed and web/bot restarted.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot
  active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 40` -> recent Jun 21 web
  restart, no new failure lines in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 40` -> recent Jun 21 bot
  restart, no new failure lines in the checked tail.

## Follow-Up Basket

- Continue the ordered go-next chain in
  [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md).
- Suggested next `/new-go-slug`: `doverabot-legacy-callback-parser-audit`.
- Keep the next slice focused on remaining direct callback parsing and stale/auth
  feedback inconsistencies outside the branches covered here.
