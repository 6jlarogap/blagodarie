# Doverabot Rental Voice STT Observability Recovery Chain

Date: 2026-06-22
Slug: `doverabot-rental-voice-stt-observability-recovery`
Status: implemented; pending runtime deploy
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)

## Recovery Purpose

Own and finish the previously uncommitted rental bot changes found in:

- `telegram-bot/handler_rental.py`
- `telegram-bot/settings.py`
- `telegram-bot/tests/test_handler_rental.py`

These changes belong to the rental voice/STT listing flow, not to the completed
`/rent/` frontend redesign chain. The active product next slug remains
`doverabot-rental-frontend-media-thumbnails`.

## Scope

- Keep rental offer/search prompts honest about voice support by mentioning
  voice only when `RENTAL_STT_URL` is configured.
- Add opt-in structured rental debug logging for STT and slot extraction.
- Improve spoken Russian date and address extraction for rental listing/search
  text.
- Return visible feedback when a voice-only rental listing message cannot be
  transcribed, instead of silently treating it as a usable listing.
- Add focused mocked bot coverage for spoken listing extraction and
  unrecognized voice handling.

## Out Of Scope

- Frontend `/rent/` changes.
- Owner web controls, reservation-history web controls, or media thumbnails.
- Backend model/API migrations.
- Local PostgreSQL test database helper work.

## Implementation

- Added `RENTAL_DEBUG_LOG_CONVERSATION` and
  `RENTAL_DEBUG_LOG_TEXT_LIMIT` defaults in bot settings.
- Added `Rental.offer_prompt()` and `Rental.search_context_prompt()` so voice
  wording follows runtime STT configuration.
- Added `Rental.log_debug()` helpers and STT response/failure logging guarded by
  the new debug setting.
- Added Russian month/day parsing plus shared date extraction for listing and
  search text.
- Improved address and availability cleanup around natural phrases such as
  "забрать на ВДНХ" and "с 1 по 3 июля".
- Changed rental voice listing handling so missing transcripts ask the user to
  resend text or a clearer voice message.
- Added tests for spoken listing slot extraction and unrecognized voice
  feedback.

## Verification

Source checks:

- `git diff --check` -> OK.
- `python3 -m unittest discover telegram-bot/tests -p 'test_handler_rental.py'`
  -> 39 tests OK; the existing mocked geocoding failure test logs the expected
  `RuntimeError: lookup failed`.
- `python3 -m compileall telegram-bot` -> OK.

Pending before final completion:

- Full mocked bot discovery.
- Django check through the deployment wrapper.
- Reindex and graphify update.
- Staged-only commit with this slug.
- Runtime deploy/status/log checks because bot runtime code changed.

## Follow-Up Basket

After this recovery chain completes, continue with the active product slug:

`doverabot-rental-frontend-media-thumbnails`
