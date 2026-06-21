# Doverabot Go Next Chain

Date: 2026-06-21
Status: slices 1-8 implemented; decision refresh active
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Current completed chain: [2026-06-21-doverabot-rental-reservation-history-controls-chain.md](2026-06-21-doverabot-rental-reservation-history-controls-chain.md)

Active next slice: Decision Refresh
Active next `/new-go-slug`: `doverabot-next-decision-refresh`
After active slice, choose and print the next `/new-go-slug`.

## Chain Purpose

Keep Doverabot implementation work moving in small `/new go` slices where each
completed chain has an explicit next suggested slug. Each slice should stay
small enough to finish with source checks, commit, deploy when runtime code
changes, and an operational handoff.

Always-visible next-slice rule:

- The top of this file must name the active next slice and the slug that should
  be run now.
- Each slice plan must name the slug to print after that slice completes.
- Each completed chain handoff must repeat the same next slug in its Follow-Up
  Basket, so the next command is visible from either file.
- When a slice is completed, advance the active next slice above to the next
  planned slice and keep the chain moving.

## Slice 1: Offer And Sympathy Feedback Coverage

Suggested `/new-go-slug`: `doverabot-offer-sympa-feedback-coverage`

Status: implemented and deployed in
[2026-06-21-doverabot-offer-sympa-feedback-coverage-chain.md](2026-06-21-doverabot-offer-sympa-feedback-coverage-chain.md).

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

Print after completion, suggested next `/new-go-slug`:
`doverabot-legacy-callback-parser-audit`

## Slice 2: Legacy Callback Parser Audit

Suggested `/new-go-slug`: `doverabot-legacy-callback-parser-audit`

Status: implemented and deployed in
[2026-06-21-doverabot-legacy-callback-parser-audit-chain.md](2026-06-21-doverabot-legacy-callback-parser-audit-chain.md).

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

Print after completion, suggested next `/new-go-slug`:
`doverabot-runtime-deeplink-consistency`

## Slice 3: Runtime Deeplink Consistency

Suggested `/new-go-slug`: `doverabot-runtime-deeplink-consistency`

Status: implemented and deployed in
[2026-06-21-doverabot-runtime-deeplink-consistency-chain.md](2026-06-21-doverabot-runtime-deeplink-consistency-chain.md).

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

Print after completion, suggested next `/new-go-slug`:
`doverabot-handler-test-harness-split`

## Slice 4: Handler Test Harness Split

Suggested `/new-go-slug`: `doverabot-handler-test-harness-split`

Status: implemented; runtime deploy not required in
[2026-06-21-doverabot-handler-test-harness-split-chain.md](2026-06-21-doverabot-handler-test-harness-split-chain.md).

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

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-v1-smoke-observability`

## Slice 5: Rental V1 Smoke Observability

Suggested `/new-go-slug`: `doverabot-rental-v1-smoke-observability`

Status: implemented; runtime deploy not required in
[2026-06-21-doverabot-rental-v1-smoke-observability-chain.md](2026-06-21-doverabot-rental-v1-smoke-observability-chain.md).

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

Print after completion, suggested next `/new-go-slug`:
`doverabot-next-decision-refresh`

## Slice 6: Next Decision Refresh

Suggested `/new-go-slug`: `doverabot-next-decision-refresh`

Status: implemented in
[2026-06-21-doverabot-next-decision-refresh-chain.md](2026-06-21-doverabot-next-decision-refresh-chain.md).

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

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-owner-listing-controls`

## Slice 7: Rental Owner Listing Controls

Suggested `/new-go-slug`: `doverabot-rental-owner-listing-controls`

Status: implemented and deployed in
[2026-06-21-doverabot-rental-owner-listing-controls-chain.md](2026-06-21-doverabot-rental-owner-listing-controls-chain.md).

Scope:

- Add an owner-facing rental listing path under `/rent` so owners can see their
  active, paused, and archived rental offers without searching as a renter.
- Expose a small owner-safe API/listing path if the bot needs it; keep owner
  authorization on `user_uuid` plus bot token and preserve existing
  `/api/rental/offer` create/get/update semantics.
- Add bot controls for pause, resume, archive, show public link, and show on
  map when coordinates exist.
- Keep this slice to listing controls only: no inventory quantities, escrow,
  geocoding, vector search, or broad reservation history UI.

Completion criteria:

- `/rent` makes own-listing management discoverable while preserving create and
  search commands.
- Owner list and status-change paths are covered by focused backend and mocked
  bot tests.
- Local bot tests, backend checks, reindex, and graph update pass.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-reservation-history-controls`

## Slice 8: Rental Reservation History Controls

Suggested `/new-go-slug`: `doverabot-rental-reservation-history-controls`

Status: implemented and deployed in
[2026-06-21-doverabot-rental-reservation-history-controls-chain.md](2026-06-21-doverabot-rental-reservation-history-controls-chain.md).

Scope:

- Add requester/owner reservation history views for open and recently closed
  rental reservations.
- Let users reopen status cards and available action buttons from history
  instead of relying only on the original Telegram notification message.
- Surface reservation event/proof audit history in concise bot text.
- Keep fake-proof consequences as an explicit later policy decision; do not
  auto-create mistrust in this slice.

Completion criteria:

- Owners and requesters can recover active reservation controls after losing
  the original bot message.
- Tests cover authorization boundaries and terminal reservation statuses.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-next-decision-refresh`
