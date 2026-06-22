# Doverabot Rental LLM Extractor Chain

Date: 2026-06-22
Slug: `doverabot-rental-llm-extractor`
Status: source implemented; runtime deploy pending
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)

## Scope

- Add an optional HTTP JSON LLM extractor for Doverabot rental offer and search
  text.
- Keep the extractor disabled unless `RENTAL_LLM_EXTRACTOR_URL` is configured.
- Preserve the current regex/date/address parser as the local fallback.
- Whitelist and normalize returned slot keys before they can affect rental
  offer/search payloads.
- Expose runtime settings for the LLM extractor through the admin wrapper.
- Keep the existing local STT timeout, debug-runtime, spoken-address, and
  freeform-availability changes that were already dirty in this worktree.

## Out Of Scope

- Adding or deploying a model-serving process.
- Adding an OpenAI/vendor SDK dependency.
- Backend schema/API changes or migrations.
- Frontend `/rent/` changes.

## Implementation

- Added `RENTAL_LLM_EXTRACTOR_*` defaults in `telegram-bot/settings.py`.
- Added LLM extractor helpers in `telegram-bot/handler_rental.py`:
  payload/header/timeout construction, response slot normalization, conservative
  merge behavior, async offer/search wrappers, and failure fallback.
- Routed `/rent_offer` and `/rent_search` text processing through the async
  extractor wrappers while keeping the synchronous parser methods for tests and
  fallback behavior.
- Extended `deploy/bin/blagodarie-admin bot-runtime-setting` with
  `RENTAL_LLM_EXTRACTOR_URL`, token, contract, model, timeout, plus
  `RENTAL_STT_TIMEOUT`.
- Added mocked rental bot tests for LLM payload/parser handling and LLM-assisted
  offer/search completion.

## Verification

Source checks:

- `python3 -m unittest discover telegram-bot/tests -p 'test_handler_rental.py'`
  -> 47 tests OK; existing mocked geocoding failure log remains expected.
- `python3 -m unittest discover telegram-bot/tests` -> 105 tests OK; existing
  mocked geocoding failure log and volatile `MemoryStorage` warning remain.
- `python3 -m compileall telegram-bot` -> OK.
- `bash -n deploy/bin/blagodarie-admin` -> OK.
- `git diff --check` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings`
  from `app/` -> OK, no issues.
- `bash scripts/reindex.sh` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK.

## Operational Handoff

Pending source commit and runtime deploy.
