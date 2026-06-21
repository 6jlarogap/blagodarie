# Doverabot Rental Owner Listing Controls Chain

Date: 2026-06-21
Status: implemented and deployed
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Slug: `doverabot-rental-owner-listing-controls`

## Scope

- Add an owner-facing rental listing path under `/rent`.
- Let owners list active, paused, and archived rental offers without searching
  as a renter.
- Add owner controls for pause, resume, archive, public bot link, and map link
  when coordinates exist.
- Keep this slice out of reservation history, inventory quantities, escrow,
  geocoding, vector search, and broader map UI changes.

## Implementation

- Extended `GET /api/rental/offer` with a bot-token-authenticated
  `owner_uuid` listing mode, preserving the existing single-offer get path and
  owner-only `PUT` status updates.
- Added `/rent_my` and made `/rent` advertise owner listing management.
- Added owner action callback payloads for pause, resume, archive, and list.
- Added owner listing cards with status text, public listing links, and map
  links for offers with coordinates.
- Added the rental commands to `handler_bot.commands_dict` so command
  interruption works while a rental FSM flow is waiting for input.

## Verification

Source checks:

- `python3 -m py_compile telegram-bot/handler_rental.py telegram-bot/handler_bot.py telegram-bot/common.py telegram-bot/tests/test_handler_rental.py telegram-bot/tests/bot_test_harness.py` -> OK.
- `python3 -m unittest discover` from `telegram-bot/tests/` -> 75 tests OK;
  emitted the existing volatile `MemoryStorage` warning in one storage test.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests --settings=app.test_settings --noinput` from `app/` -> 9 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> OK,
  no issues.
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations --check --dry-run` from `app/` -> no changes detected; Django also emitted a sandbox-local migration-history socket warning while the command still exited 0.
- `git diff --check` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK; final AST graph rebuilt with 4424 nodes, 8855 edges, and 441 communities.

Commit:

- `git commit -m "doverabot-rental-owner-listing-controls"` -> `ae72341`.

Runtime handoff:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply;
  existing `security.W002` clickjacking middleware warning remains.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test
  successful; existing `security.W002` warning remains.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with the same
  existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot
  all active.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx active; gunicorn
  and Telegram bot restarted at 2026-06-21 14:29 MSK and active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 120` and `logs-bot 120`
  -> expected restart history; old Jun 16 failures still appear in the wider
  tail, with no new traceback after the 14:29 MSK restart.

Public smoke checks:

- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'` -> HTTP 200, `{"offers":[]}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/user/points/?rental=on'` -> HTTP 200, empty `points`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/offer/'` -> expected HTTP 404 without `uuid`/`offer_id`.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-reservation-history-controls`
