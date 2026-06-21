# Doverabot Go Next Chain

Date: 2026-06-21
Status: planned
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Current completed chain: [2026-06-21-doverabot-profile-edit-state-feedback-finish-chain.md](2026-06-21-doverabot-profile-edit-state-feedback-finish-chain.md)

## Chain Purpose

Keep Doverabot implementation work moving in small `/new go` slices where each
completed chain has an explicit next suggested slug. Each slice should stay
small enough to finish with source checks, commit, deploy when runtime code
changes, and an operational handoff.

## Slice 1: Offer And Sympathy Feedback Coverage

Suggested `/new-go-slug`: `doverabot-offer-sympa-feedback-coverage`

Scope:

- Add mocked coverage around legacy `/offer`, donation, and sympathy callback
  failure paths in `telegram-bot/handler_offer.py` and
  `telegram-bot/handler_sympas.py`.
- Prefer user-visible stale/auth/API feedback over silent returns or bare
  callback acknowledgements when a button is expired, malformed, or no longer
  authorized.
- Cover command interruption in offer/sympathy FSM message handlers where a
  new command arrives while the bot waits for text/media.
- Keep successful offer, donate, sympathy, and message-delivery behavior
  unchanged.

Completion criteria:

- Targeted mocked tests cover malformed payload, auth failure, API failure or
  missing-state exits, and command interruption for touched flows.
- Local bot tests and syntax checks pass.
- Runtime code changes are committed, deployed, and logged.

Suggested next `/new-go-slug`: `doverabot-legacy-callback-parser-audit`

## Slice 2: Legacy Callback Parser Audit

Suggested `/new-go-slug`: `doverabot-legacy-callback-parser-audit`

Scope:

- Audit non-rental handlers for direct callback parsing, duplicate callback
  function names, and inconsistent stale/auth handling.
- Consolidate any remaining parsing into `Misc.parse_callback_data`,
  `Misc.callback_part`, typed local parsers, or existing flow-specific helpers.
- Keep payload formats backwards compatible unless a stale button can be
  rejected before API/FSM work.
- Add focused mocked tests for every edited branch.

Completion criteria:

- No newly touched branch relies on ad hoc callback parsing.
- Duplicate handler names in touched areas are resolved or explicitly recorded
  if left out of scope.
- Local bot tests and syntax checks pass.
- Runtime code changes are committed, deployed, and logged.

Suggested next `/new-go-slug`: `doverabot-runtime-deeplink-consistency`

## Slice 3: Runtime Deeplink Consistency

Suggested `/new-go-slug`: `doverabot-runtime-deeplink-consistency`

Scope:

- Audit newly touched bot flows for hard-coded bot usernames, Telegram links,
  and Doverabot host assumptions.
- Prefer `Misc.get_deeplink`, `Misc.get_deeplink_with_name`, `bot_data.username`,
  and configured hosts over literal `t.me/doverabot` or duplicated URL logic.
- Add regression tests for any changed links.
- Keep user-facing link text and existing deep-link payloads compatible.

Completion criteria:

- Touched bot flows generate links from runtime/configured values.
- Tests pin at least one representative deep-link path in each edited module.
- Local bot tests and syntax checks pass.
- Runtime code changes are committed, deployed, and logged.

Suggested next `/new-go-slug`: `doverabot-handler-test-harness-split`

## Slice 4: Handler Test Harness Split

Suggested `/new-go-slug`: `doverabot-handler-test-harness-split`

Scope:

- Split the growing mocked bot test surface into clearer per-domain files
  without weakening import stubs or coverage.
- Preserve existing tests before moving code.
- Keep this mostly mechanical: avoid behavioral changes except for tiny fixes
  needed to keep tests deterministic.

Completion criteria:

- Existing bot tests still pass after the split.
- New test files are named by handler domain and remain runnable through
  `python3 -m unittest discover telegram-bot/tests`.
- No runtime deploy is needed unless production code changes.

Suggested next `/new-go-slug`: `doverabot-rental-v1-smoke-observability`

## Slice 5: Rental V1 Smoke Observability

Suggested `/new-go-slug`: `doverabot-rental-v1-smoke-observability`

Scope:

- Add or document low-friction smoke checks for rental search, map exposure,
  booking/reservation callback surfaces, and payment-proof handoff.
- Prefer source-level mocked tests and wrapper-compatible curl smoke commands.
- Do not expand rental V1 scope into escrow, conflict tracking, geocoding, or
  vector search.

Completion criteria:

- The rental V1 runtime handoff has repeatable checks for the public surfaces
  most likely to regress.
- Any new source tests pass locally.
- Runtime code changes, if any, are committed, deployed, and logged.

Suggested next `/new-go-slug`: `doverabot-next-decision-refresh`

## Slice 6: Next Decision Refresh

Suggested `/new-go-slug`: `doverabot-next-decision-refresh`

Scope:

- Re-read the active Doverabot project note, completed chain references, and
  current source/test state.
- Decide whether the next work should stay on legacy hardening, return to
  rental V1, or move to a new product slice.
- Update this go-next chain and the parent project note so the latest completed
  chain again suggests a concrete next slug.

Completion criteria:

- The project note names the active next implementation slice.
- The latest completed chain points to that slug.
- Any obsolete slice suggestions are marked done, superseded, or deferred.

Suggested next `/new-go-slug`: to be chosen during this refresh.
