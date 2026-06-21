# Doverabot Rental Map Query Link Polish Chain

Date: 2026-06-21
Slug: `doverabot-rental-map-query-link-polish`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state

## Scope

- Improve source-owned rental map behavior without editing generated
  `frontend/*/dist/` bundles.
- Make bot `Show on map` links carry useful rental query parameters such as
  equipment, dates, price ceiling, trusted-only, and selected rental UUID when
  known.
- Ensure `/api/user/points?rental=on` and `with_rentals=on` honor those
  parameters consistently and keep private/mistrusted listings hidden.
- Document frontend limitations that cannot be solved without editable map
  source or generated-bundle deployment.

## Implementation

- Extended bot rental map URLs with source-owned query params:
  `rental_uuid`, `rental_query`, `rental_equipment_type`, `rental_date_from`,
  `rental_date_to`, `rental_price_max`, and `rental_trusted_only`.
- Threaded structured search params into search-result map links while keeping
  existing Reserve/Contact/Show-on-map result cards compatible.
- Added map links to reservation history cards when the related offer has
  coordinates, carrying reservation dates.
- Owner listing map links now include listing equipment, availability dates,
  and price where available.
- Confirmed `with_rentals=on` uses the same `append_rental_points` and
  `apply_rental_map_filters` path as `rental=on`.
- Generated frontend bundles were not edited; deeper map UI behavior remains
  limited by the absence of editable map source in this workspace.

## Verification

Source checks:

- `PYTHONPATH=telegram-bot/tests python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 30 tests OK.
- `PYTHONPATH=telegram-bot/tests python3 -m unittest discover telegram-bot/tests` -> 88 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests.test_rental_map_points_have_marker_payload_and_filters users.tests.ApiRentalOfferTests.test_rental_map_with_rentals_honors_filters_and_mistrust --settings=app.test_settings --noinput` from `app/` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests --settings=app.test_settings --noinput` from `app/` -> 15 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings` from `app/` -> OK, no issues.
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations users --check --dry-run --settings=app.test_settings` from `app/` -> OK, no changes detected; emitted the same local PostgreSQL socket permission warning while checking migration history.
- `python3 -m compileall telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py` -> OK.
- `git diff --check` -> OK.

Public read-only smoke commands:

- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'` -> HTTP 200, `{"offers":[]}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/user/points/?rental=on&rental_query=tent&rental_price_max=600'` -> HTTP 200, empty `points`.

Runtime handoff:

- Runtime `sync`, `migrate`, and `deploy` were not run for this slice because
  the active `/usr/local/sbin/blagodarie-admin` wrapper still has the blocker
  recorded in
  [2026-06-21-doverabot-rental-proof-dispute-controls-chain.md](2026-06-21-doverabot-rental-proof-dispute-controls-chain.md):
  its dry-run would sync unrelated untracked local state, and installing the
  repo wrapper exclusion is blocked by sudo authentication.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-inventory-quantity-groundwork`
