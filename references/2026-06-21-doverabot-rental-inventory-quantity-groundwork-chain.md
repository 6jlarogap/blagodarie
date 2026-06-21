# Doverabot Rental Inventory Quantity Groundwork Chain

Date: 2026-06-21
Slug: `doverabot-rental-inventory-quantity-groundwork`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state

## Scope

- Decide and implement the smallest safe model for one listing representing
  multiple identical rentable items.
- Add quantity fields and overlap/capacity checks only if needed; preserve
  current one-listing-as-one-item behavior by default.
- Keep owner UX minimal: creation/update payloads, owner listing text, and
  reservation availability checks.
- Do not add per-item serial tracking, deposits, escrow, or complex inventory
  calendars.

## Implementation

- Added `RentalOffer.quantity_total` with default `1`.
- Included quantity in rental offer API payloads and create/update validation.
- Changed overlap enforcement so each reservation consumes one unit and
  overlapping reservations are allowed until `quantity_total` capacity is
  reached.
- Extended rental listing slot extraction to parse quantity from owner text.
- Added quantity display to public and owner listing cards only when quantity
  is greater than one.

## Verification

Source checks:

- `PYTHONPATH=telegram-bot/tests python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 31 tests OK.
- `PYTHONPATH=telegram-bot/tests python3 -m unittest discover telegram-bot/tests` -> 89 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests.test_create_rental_offer users.tests.ApiRentalOfferTests.test_owner_listing_controls_include_paused_archived_and_status_updates users.tests.ApiRentalOfferTests.test_quantity_capacity_allows_overlaps_up_to_listing_quantity users.tests.ApiRentalOfferTests.test_timed_hold_requires_dates_and_rejects_overlap_until_expired --settings=app.test_settings --noinput` from `app/` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests --settings=app.test_settings --noinput` from `app/` -> 16 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings` from `app/` -> OK, no issues.
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations users --check --dry-run --settings=app.test_settings` from `app/` -> OK, no changes detected; emitted the same local PostgreSQL socket permission warning while checking migration history.
- `python3 -m compileall telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py` -> OK.
- `git diff --check` -> OK.

Runtime handoff:

- Runtime `sync`, `migrate`, and `deploy` were not run for this slice because
  the active `/usr/local/sbin/blagodarie-admin` wrapper still has the blocker
  recorded in
  [2026-06-21-doverabot-rental-proof-dispute-controls-chain.md](2026-06-21-doverabot-rental-proof-dispute-controls-chain.md):
  its dry-run would sync unrelated untracked local state, and installing the
  repo wrapper exclusion is blocked by sudo authentication.
- The schema migration `users.0062_rentaloffer_quantity_total` is committed in
  source and still needs runtime migration once deployment is unblocked.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-geocoding-contract`
