# Doverabot Rental Voice Listing Clarifications Chain

Date: 2026-06-21
Slug: `doverabot-rental-voice-listing-clarifications`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state

## Scope

- Improve `/rent_offer` voice/text listing creation so the bot asks concise
  follow-up questions for missing core fields instead of accepting a weak
  one-message listing.
- Reuse the existing Organizm/Hermes STT helpers and durable FSM state.
- Start with title/item, place or coordinates, dates/availability, price terms,
  and optional media; do not add geocoding in this slice.
- Keep successful current one-message listing creation compatible when enough
  information is present.

## Implementation

- Extended rental offer slot extraction to parse dates/availability alongside
  title, address, coordinates, and price text.
- Added rental offer FSM slot accumulation so partial listing text is kept in
  durable state across follow-up replies.
- Added concise missing-field prompts for item, place/coordinates,
  availability, and price before calling the rental offer API.
- Kept media/message creation compatible: once the accumulated slots are
  complete, the final message still supplies `tgdesc` and the normal create or
  update path runs.

## Verification

Source checks:

- `PYTHONPATH=telegram-bot/tests python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 26 tests OK.
- `PYTHONPATH=telegram-bot/tests python3 -m unittest discover telegram-bot/tests` -> 84 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings` from `app/` -> OK, no issues.
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
`doverabot-rental-voice-search-refinement`
