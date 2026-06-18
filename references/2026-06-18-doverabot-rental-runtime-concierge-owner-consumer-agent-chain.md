# Doverabot Rental Runtime Concierge Owner Consumer Agent Chain

Date: 2026-06-18
Status: implemented and deployed
Parent chain: [doverabot-rental-offers-chain.md](doverabot-rental-offers-chain.md)
Started `/new-go-slug`: `doverabot-rental-runtime-concierge-owner-consumer-agent`
Suggested next `/new-go-slug`: `doverabot-rental-durable-fsm-hermes-map-marker-tests`

## Scope

Turn the rental reservation handoff from a one-shot notification into a bot-mediated runtime flow between the consumer and owner.

Implemented:

- Added `RentalReservationEvent` for an audited reservation event journal.
- Added bot-facing `PUT /api/rental/reservation/` actions:
  - `owner_accept`
  - `payment_reported`
  - `owner_confirm`
  - `cancel`
- Kept authorization in the backend:
  - only the owner can accept and confirm;
  - only the requester can report payment;
  - either participant can cancel before the reservation is terminal.
- Preserved active reservation identity across repeated booking taps for `sent`, `owner_accepted`, and `payment_reported` statuses.
- Added owner and consumer inline keyboards to the Telegram runtime flow.
- Added owner/consumer Telegram notifications after each reservation action.
- Added backend tests for the runtime action chain.

## Verification

Passed:

- `python3 -m py_compile app/users/models.py app/users/views.py app/users/tests.py app/users/migrations/0059_rentalreservationevent.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check`
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations --check --dry-run`
- `git commit -m "doverabot-rental-runtime-concierge-owner-consumer-agent"` -> `5ff91f0`
- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run`
- `sudo -n /usr/local/sbin/blagodarie-admin sync`
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> applied `users.0059_rentalreservationevent`
- `sudo -n /usr/local/sbin/blagodarie-admin deploy`
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, bot active
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'` -> HTTP 200
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 80`
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 80`

Blocked:

- `/srv/blagodarie/venv-app/bin/python manage.py test users`

Reason: the sandboxed run cannot access the local PostgreSQL socket; the unsandboxed run reaches PostgreSQL but peer authentication rejects the current OS user for database user `postgres`. `sudo -n -u postgres ...` is unavailable because sudo requires interactive authentication.

Deploy notes:

- Django deploy check reports the pre-existing `security.W002` clickjacking middleware warning.
- Recent web/bot logs after deploy show service restarts and no new traceback in the checked tail; older June 16 permission errors remain in the 80-line journal window.

## Follow-Up Basket

Next `/new-go-slug`: `doverabot-rental-durable-fsm-hermes-map-marker-tests`

Recommended next chain:

- Replace rental bot `MemoryStorage` dependency with durable FSM storage before long-running rental conversations rely on bot process memory.
- Verify and lock the real Organizm/Hermes STT contract for rental voice search.
- Decide whether deployed map UI needs a frontend marker/filter change for rental points.
- Add aiogram-level handler tests/mocks for rental callbacks, command interruption, and owner-consumer notification failures.
- Run the DB-backed Django tests in an environment with PostgreSQL test database permissions.
