# Doverabot Rental Reservation History Controls Chain

Date: 2026-06-21
Status: implemented and deployed
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Slug: `doverabot-rental-reservation-history-controls`

## Scope

- Add requester/owner reservation history views for open and recently closed
  rental reservations.
- Let users recover status cards and available action buttons from history
  instead of relying only on the original Telegram notification.
- Surface reservation event/proof audit history in concise bot text.
- Keep fake-proof consequences as an explicit later policy decision.

## Implementation

- Added bot-token-authenticated `GET /api/rental/reservation` history listing
  with `user_uuid`, `role=requester|owner|all`, `status_group=open|recent_closed|all`,
  optional `status`, optional `reservation_id`, and bounded `number`.
- Reused the existing reservation detail payload for history cards and added
  `viewer_role` so the bot can render requester or owner controls per row.
- Moved expired `sent`, `awaiting_payment`, and `owner_accepted` holds into
  `expired` before history listing, so stale accepted holds do not render as
  active cards.
- Added `/rent_history`, made `/rent` advertise it, and wired command
  interruption through `handler_bot.commands_dict`.
- Added history cards with open/recent-closed sections, role-aware action
  markup, date/status text, and concise event/payment-proof audit summaries.
- Allowed owner reservation cards in `awaiting_payment` to show the existing
  owner-accept action, matching the backend state machine.

## Verification

Source checks:

- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_bot.py telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py` -> OK.
- `python3 telegram-bot/tests/test_handler_rental.py` -> 19 tests OK.
- `/srv/blagodarie/venv-app/bin/python -m py_compile users/views.py users/tests.py` from `app/` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> OK, no issues.
- `/srv/blagodarie/venv-app/bin/python manage.py test users` from `app/` -> blocked before tests by local PostgreSQL peer authentication: `FATAL:  Peer authentication failed for user "postgres"`.
- `git diff --check` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK; final AST graph rebuilt with 4445 nodes, 8901 edges, and 440 communities.

Commit:

- `git commit -m "doverabot-rental-reservation-history-controls"` -> `3b75b0c`.
- `git commit -m "doverabot-rental-reservation-history-controls handoff"` -> `644bc7c`.

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
  and Telegram bot restarted at 2026-06-21 14:47 MSK and active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 120` and `logs-bot 120`
  -> expected restart history with no new traceback after the 14:47 MSK restart.

Public smoke checks:

- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/reservation/?tg_token=bad&user_uuid=00000000-0000-0000-0000-000000000000'` -> expected HTTP 400, `{"message":"Неверный токен телеграм бота"}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'` -> HTTP 200, `{"offers":[]}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/user/points/?rental=on'` -> HTTP 200, empty `points`.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-next-decision-refresh`
