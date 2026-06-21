# Doverabot Rental Geocoding Contract Chain

Date: 2026-06-21
Slug: `doverabot-rental-geocoding-contract`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state

## Scope

- Add a narrow, configurable geocoding contract for rental addresses without
  making any provider mandatory.
- Use mocked provider tests; production should degrade cleanly when no provider
  is configured.
- Offer address-to-coordinate suggestions for listing/search only after
  explicit user confirmation.
- Keep map visibility rules unchanged and do not leak private or mistrusted
  listings through geocoding results.

## Implementation

- Added optional bot settings for the `doverabot_rental_geocoding_v1` adapter:
  URL, token, result limit, and search bounding-box delta.
- Added rental geocoding adapter helpers that send provider JSON only when a
  URL is configured, parse common result/suggestion response shapes, validate
  coordinate ranges, and degrade to no suggestions on missing provider or
  failed lookup.
- Added rental geocode callback namespace `85` with explicit `offer` and
  `search` confirmation actions.
- Listing creation now prompts with address-coordinate suggestions before API
  create/update when an address has no coordinates; coordinates are added to
  the saved payload only after the user confirms a suggestion.
- Rental search now prompts before using geocoded coordinates and, after
  confirmation, sends a bounded lat/lng search window through the existing
  rental search API filters.
- No backend visibility or map exposure rules were changed.

## Verification

Source checks:

- `python3 -m unittest discover telegram-bot/tests -p 'test_handler_rental.py'` -> 37 tests OK.
- `python3 -m unittest discover telegram-bot/tests` -> 95 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> OK, no issues.
- `python3 -m compileall telegram-bot/handler_rental.py telegram-bot/common.py telegram-bot/settings.py telegram-bot/tests/test_handler_rental.py telegram-bot/tests/bot_test_harness.py` -> OK.
- `git diff --check` -> OK.
- `bash scripts/reindex.sh` -> OK; rebuilt local CODE_INDEX pyramid.
- `uv tool run --from graphifyy graphify update .` -> OK; rebuilt AST graph with 4565 nodes, 9091 edges, and 448 communities.

Runtime handoff:

- Runtime `sync`, `migrate`, and `deploy` were not run for this slice because
  the active `/usr/local/sbin/blagodarie-admin` wrapper still has the blocker
  recorded in
  [2026-06-21-doverabot-rental-proof-dispute-controls-chain.md](2026-06-21-doverabot-rental-proof-dispute-controls-chain.md):
  its dry-run would sync unrelated untracked local state, and installing the
  repo wrapper exclusion is blocked by sudo authentication.
- No schema migration was added in this slice.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-semantic-search-ranking`
