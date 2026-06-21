# Doverabot Legacy Callback Parser Audit Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-legacy-callback-parser-audit`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)

## Scope

Audit non-rental legacy callback parsing and finish a small hardening slice:

- find remaining direct non-rental callback data splits and duplicate handler names;
- consolidate edited ad hoc parsing into typed local parsers;
- reject malformed stale buttons before owner/API/FSM work where possible;
- add focused mocked tests for every edited branch.

## Implemented

- Confirmed no duplicate callback handler names in `telegram-bot/handler_*.py`.
- Confirmed no remaining non-rental direct `callback.data.split(KeyboardType.SEP)`
  calls; only the shared helper and prior rental-local parsers remain.
- Added a typed sympathy common callback parser for SID pair plus journal ID
  payloads, so malformed or missing journal IDs now return a stale callback
  notice before profile lookups.
- Added a typed meet action callback parser for meet enter/revoke payloads,
  preserving optional inviter SID handling without inline raw part parsing.
- Added mocked bot coverage for malformed sympathy journal payloads, malformed
  meet action callbacks, and the valid meet action inviter SID path.

## Verification

Passed before source commit:

- `python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 64 tests OK.
- `python3 -m unittest discover telegram-bot/tests` -> 64 tests OK.
- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_callbacks.py telegram-bot/handler_relatives.py telegram-bot/handler_bot.py telegram-bot/handler_offer.py telegram-bot/handler_sympas.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> no issues.
- `git diff --check`
- `uv tool run --from graphifyy graphify update .` -> rebuilt code graph.

Audit commands:

- Non-rental split scan found no direct splits outside shared/rental parser code.
- AST duplicate-name scan over `telegram-bot/handler_*.py` returned no duplicates.

## Operational Handoff

Source commit:

- `git commit -m "doverabot-legacy-callback-parser-audit"` -> `2b317dc`

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
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 60` -> recent Jun 21 web
  restart, no traceback in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 80` -> recent Jun 21 bot
  restart, no traceback in the checked tail.

## Follow-Up Basket

- Continue the ordered go-next chain in
  [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md).
- Suggested next `/new-go-slug`: `doverabot-runtime-deeplink-consistency`.
