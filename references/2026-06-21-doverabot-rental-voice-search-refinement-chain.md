# Doverabot Rental Voice Search Refinement Chain

Date: 2026-06-21
Slug: `doverabot-rental-voice-search-refinement`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state

## Scope

- Improve `/rent_search` voice/text search so the bot asks for missing
  constraints and then issues a structured search request.
- Preserve existing taxonomy clarification for ambiguous equipment terms.
- Include date, location/context text, price ceiling, trusted-only, and map
  intent where they can be parsed without geocoding.
- Keep result cards compatible with existing Reserve, Contact, and Show on map
  buttons.

## Implementation

- Extended rental search slot extraction with price ceiling, trusted-only, and
  map-intent parsing while preserving date/context parsing.
- Carried structured search slots through the FSM and into
  `Rental.search_with_params`.
- Added `/api/rental/search` support for `price_max` and `trusted_only` filters
  using the existing rental visibility/trust helpers.
- Preserved ambiguous equipment clarification behavior and existing result-card
  rendering.

## Verification

Source checks:

- `PYTHONPATH=telegram-bot/tests python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 29 tests OK.
- `PYTHONPATH=telegram-bot/tests python3 -m unittest discover telegram-bot/tests` -> 87 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests.test_search_filters_price_and_trusted_only users.tests.ApiRentalOfferTests.test_taxonomy_tags_offer_and_asks_for_ambiguous_board --settings=app.test_settings --noinput` from `app/` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests --settings=app.test_settings --noinput` from `app/` -> 14 tests OK.
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

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-map-query-link-polish`
