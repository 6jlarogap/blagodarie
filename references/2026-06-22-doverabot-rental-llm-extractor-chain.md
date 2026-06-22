# Doverabot Rental LLM Extractor Chain

Date: 2026-06-22
Slug: `doverabot-rental-llm-extractor`
Status: runtime source deployed; wrapper install blocked for new runtime keys
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
- Tracked the existing `.graphifyignore` so graphify/deploy ignore state is not
  left as an untracked source file.

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

Source commit:

- `00e9ec8` `doverabot-rental-llm-extractor`

Deploy checks:

- `sudo bash deploy/install-blagodarie-admin-workflow.sh` -> blocked:
  `sudo: A terminal is required to authenticate`.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> passed with the
  existing Django `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> completed and
  showed source differences to sync, including the pre-existing untracked
  `.graphifyignore`.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> completed; Django check
  reported the existing `security.W002` warning and nginx syntax was OK.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, bot, and
  rental STT all active.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx active, gunicorn
  restarted at 2026-06-22 19:41:56 MSK, telegram-bot restarted at
  2026-06-22 19:41:57 MSK, rental STT active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 80` and
  `logs-bot 80` -> recent tails show service restart entries; older rental
  debug lines remain in history.
- `sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting status all`
  -> old installed wrapper reports only the prior runtime keys and does not yet
  expose `RENTAL_LLM_EXTRACTOR_*` or `RENTAL_STT_TIMEOUT`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n'
  'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'` -> HTTP
  200, `{"offers":[]}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n'
  'https://map.doverabot.ru/rent/'` -> HTTP 200.

No migrations were added or required.

Remaining blocker:

- Installing the updated `/usr/local/sbin/blagodarie-admin` wrapper requires
  sudo authentication. Until the maintainer reruns
  `sudo bash deploy/install-blagodarie-admin-workflow.sh`, the deployed bot code
  stays disabled-by-default for LLM extraction, but the convenience
  `bot-runtime-setting` command cannot set the new LLM extractor keys.
