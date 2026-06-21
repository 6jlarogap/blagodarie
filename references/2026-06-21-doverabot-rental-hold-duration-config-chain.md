# Doverabot Rental Hold Duration Config Chain

Date: 2026-06-21
Slug: `doverabot-rental-hold-duration-config`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state

## Scope

- Replace the hard-coded 10 minute reservation hold with a runtime setting,
  defaulting to the current 600 seconds.
- Keep this slice system-level only: no owner/listing duration UI or schema.
- Make reservation creation events, API responses, and bot text use the
  configured value consistently.
- Keep overlap, expiration, and payment-proof behavior otherwise unchanged.

## Implementation

- Added `ApiRentalMixin.reservation_hold_seconds()` backed by
  `settings.RENTAL_RESERVATION_HOLD_SECONDS`, defaulting to 600 seconds and
  clamping invalid/zero values to at least one second.
- Reservation creation now uses the runtime hold duration for
  `hold_expires_at` and for the audited creation-event `hold_seconds` payload.
- Reservation API payloads now expose `reservation.hold_seconds` in addition to
  `hold_seconds_remaining`.
- Bot reservation text now prefers API-provided `hold_seconds`, falling back to
  remaining seconds for compatibility with older responses.

## Verification

Source checks:

- `PYTHONPATH=telegram-bot/tests python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 22 tests OK.
- `PYTHONPATH=telegram-bot/tests python3 -m unittest discover telegram-bot/tests` -> 80 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests.test_timed_hold_requires_dates_and_rejects_overlap_until_expired users.tests.ApiRentalOfferTests.test_reservation_hold_duration_uses_runtime_setting --settings=app.test_settings --noinput` from `app/` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests --settings=app.test_settings --noinput` from `app/` -> 13 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings` from `app/` -> OK, no issues.
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations users --check --dry-run --settings=app.test_settings` from `app/` -> OK, no changes detected; emitted the same local PostgreSQL socket permission warning while checking migration history.
- `python3 -m compileall telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py` -> OK.
- `bash scripts/reindex.sh` -> OK; rebuilt local CODE_INDEX pyramid.
- `git diff --check` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK; rebuilt AST graph with 4496 nodes, 8962 edges, and 448 communities.

Runtime handoff:

- Runtime `sync`, `migrate`, and `deploy` were not run for this slice because
  the active `/usr/local/sbin/blagodarie-admin` wrapper still has the blocker
  recorded in
  [2026-06-21-doverabot-rental-proof-dispute-controls-chain.md](2026-06-21-doverabot-rental-proof-dispute-controls-chain.md):
  its dry-run would sync unrelated untracked local state, and installing the
  repo wrapper exclusion is blocked by sudo authentication.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-voice-listing-clarifications`
