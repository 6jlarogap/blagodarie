# Doverabot Handler Test Harness Split Chain

Date: 2026-06-21
Status: implemented; runtime deploy not required
Started `/new-go-slug`: `doverabot-handler-test-harness-split`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Prior chain: [2026-06-21-doverabot-runtime-deeplink-consistency-chain.md](2026-06-21-doverabot-runtime-deeplink-consistency-chain.md)

## Scope

Split the growing mocked Telegram bot test surface into clearer per-domain files
without weakening the import stubs or test coverage:

- preserve the existing 68 mocked bot tests;
- move shared aiogram/settings/common/fake Telegram stubs into a reusable test
  harness module;
- keep test files named by handler domain and runnable through
  `python3 -m unittest discover telegram-bot/tests`;
- avoid runtime behavior changes.

## Implemented

- Added `telegram-bot/tests/bot_test_harness.py` with the shared dependency
  stubs, fake Telegram message/callback/bot objects, and fresh-import helper.
- Split the former monolithic `test_handler_rental.py` classes into:
  - `test_common.py`
  - `test_handler_callbacks_profile.py`
  - `test_handler_offer_sympa.py`
  - `test_handler_relatives.py`
  - `test_handler_rental.py`
  - `test_main.py`
- Kept `test_handler_rental.py` focused on rental handler coverage.
- Kept runtime modules untouched; no migration or deploy path was needed.

## Verification

Passed before source commit:

- `python3 -m unittest discover telegram-bot/tests` -> 68 tests OK.
- `python3 -m compileall telegram-bot`
- `bash scripts/reindex.sh`
- `uv tool run --from graphifyy graphify update .`

## Operational Handoff

Source commit:

- `git commit -m "doverabot-handler-test-harness-split"`

Deploy checks:

- Runtime deploy skipped because this slice changed only tests, docs, indexes,
  and graph metadata; no production code or migrations changed.

## Follow-Up Basket

- Continue the ordered go-next chain in
  [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md).
- Suggested next `/new-go-slug`: `doverabot-rental-v1-smoke-observability`.
- After `doverabot-rental-v1-smoke-observability`, print
  `doverabot-next-decision-refresh`.
