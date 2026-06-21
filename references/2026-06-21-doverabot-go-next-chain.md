# Doverabot Go Next Chain

Date: 2026-06-21
Status: slices 1-14 source-implemented; runtime deploy blocked since slice 10; slices 15-17 planned; rental inventory quantity groundwork active
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Current completed chain: [2026-06-21-doverabot-rental-map-query-link-polish-chain.md](2026-06-21-doverabot-rental-map-query-link-polish-chain.md)

Active next slice: Rental Inventory Quantity Groundwork
Active next `/new-go-slug`: `doverabot-rental-inventory-quantity-groundwork`
After active slice, advance to the next planned slice and print its
`/new-go-slug`; do not run another decision refresh until this saved sequence is
exhausted or new production facts invalidate it.

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
- When this saved sequence is exhausted, use `doverabot-next-decision-refresh`
  to re-read source state and choose the next batch.

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

## Slice 9: Next Decision Refresh After Reservation History

Suggested `/new-go-slug`: `doverabot-next-decision-refresh`

Status: implemented in
[2026-06-21-doverabot-next-decision-refresh-after-reservation-history-chain.md](2026-06-21-doverabot-next-decision-refresh-after-reservation-history-chain.md).

Scope:

- Re-read the active Doverabot project note, completed owner-listing and
  reservation-history references, and current source/test state.
- Decide the next small source-owned product slice after owner listing and
  reservation history are done.
- Update this go-next chain and the parent project note so the latest completed
  chain again suggests a concrete next slug.

Completion criteria:

- The project note names the active next implementation slice.
- The latest completed chain points to that slug.
- Any obsolete slice suggestions are marked done, superseded, or deferred.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-proof-dispute-controls`

## Slice 10: Rental Proof Dispute Controls

Suggested `/new-go-slug`: `doverabot-rental-proof-dispute-controls`

Status: source implemented; runtime deploy blocked in
[2026-06-21-doverabot-rental-proof-dispute-controls-chain.md](2026-06-21-doverabot-rental-proof-dispute-controls-chain.md).

Scope:

- Add an owner-only reservation action for unacceptable or fake payment proof
  after a requester submits proof.
- Record a distinct audited event so `/rent_history` can tell proof disputes
  apart from generic cancellations.
- Release the reserved date interval by moving the reservation to a terminal
  state, without auto-creating mistrust or reputation penalties.
- Update owner/requester bot text and action markup so the owner can reject
  proof, and users understand trust/mistrust remains a separate profile action.

Completion criteria:

- Backend tests cover owner authorization, requester denial, event history, and
  terminal status behavior.
- Mocked bot tests cover owner markup, callback handling, and notification text.
- Local bot tests, backend checks, reindex, and graph update pass.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-hold-duration-config`

## Slice 11: Rental Hold Duration Config

Suggested `/new-go-slug`: `doverabot-rental-hold-duration-config`

Status: source implemented; runtime deploy blocked in
[2026-06-21-doverabot-rental-hold-duration-config-chain.md](2026-06-21-doverabot-rental-hold-duration-config-chain.md).

Scope:

- Replace the hard-coded 10 minute reservation hold with a runtime setting,
  defaulting to the current 600 seconds.
- Keep this slice system-level only: no owner/listing-specific duration UI or
  schema yet.
- Make reservation creation events, API responses, and bot text use the
  configured value consistently.
- Keep overlap, expiration, and payment-proof behavior otherwise unchanged.

Completion criteria:

- Backend tests cover the default hold duration and an overridden setting.
- Mocked bot tests cover hold-duration text from API payloads.
- No migration is required unless implementation evidence proves otherwise.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-voice-listing-clarifications`

## Slice 12: Rental Voice Listing Clarifications

Suggested `/new-go-slug`: `doverabot-rental-voice-listing-clarifications`

Status: source implemented; runtime deploy blocked in
[2026-06-21-doverabot-rental-voice-listing-clarifications-chain.md](2026-06-21-doverabot-rental-voice-listing-clarifications-chain.md).

Scope:

- Improve `/rent_offer` voice/text listing creation so the bot asks concise
  follow-up questions for missing core fields instead of accepting a weak
  one-message listing.
- Reuse the existing Organizm/Hermes STT helpers and durable FSM state.
- Start with title/item, place or coordinates, dates/availability, price terms,
  and optional media; do not add geocoding in this slice.
- Keep successful current one-message listing creation compatible when enough
  information is present.

Completion criteria:

- Mocked bot tests cover voice transcript slot extraction, missing-field
  prompts, command interruption, and final API payload.
- Backend tests cover any new normalized fields or validation rules.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-voice-search-refinement`

## Slice 13: Rental Voice Search Refinement

Suggested `/new-go-slug`: `doverabot-rental-voice-search-refinement`

Status: source implemented; runtime deploy blocked in
[2026-06-21-doverabot-rental-voice-search-refinement-chain.md](2026-06-21-doverabot-rental-voice-search-refinement-chain.md).

Scope:

- Improve `/rent_search` voice/text search so the bot asks for missing
  constraints and then issues a structured search request.
- Preserve existing taxonomy clarification for ambiguous equipment terms.
- Include date, location/context text, price ceiling, trusted-only, and map
  intent where they can be parsed without geocoding.
- Keep result cards compatible with existing Reserve, Contact, and Show on map
  buttons.

Completion criteria:

- Mocked bot tests cover missing-context prompts, date/price/trusted-only slot
  extraction, ambiguous equipment clarification, and command interruption.
- Backend tests cover any new search query parameters or parser expectations.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-map-query-link-polish`

## Slice 14: Rental Map Query Link Polish

Suggested `/new-go-slug`: `doverabot-rental-map-query-link-polish`

Status: source implemented; runtime deploy blocked in
[2026-06-21-doverabot-rental-map-query-link-polish-chain.md](2026-06-21-doverabot-rental-map-query-link-polish-chain.md).

Scope:

- Improve source-owned rental map behavior without editing generated
  `frontend/*/dist/` bundles.
- Make bot `Show on map` links carry useful rental query parameters such as
  equipment, dates, price ceiling, trusted-only, and selected rental UUID when
  known.
- Ensure `/api/user/points?rental=on` and `with_rentals=on` honor those
  parameters consistently and keep private/mistrusted listings hidden.
- Document any frontend limitation that cannot be solved without editable map
  source or an explicit generated-bundle deployment.

Completion criteria:

- Backend tests cover rental map filters, mistrust hiding, private listing
  hiding, and URL parameter compatibility.
- Mocked bot tests cover generated map links from search/history/listing cards.
- Public read-only smoke commands are recorded for rental search and map points.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-inventory-quantity-groundwork`

## Slice 15: Rental Inventory Quantity Groundwork

Suggested `/new-go-slug`: `doverabot-rental-inventory-quantity-groundwork`

Status: planned

Scope:

- Decide and implement the smallest safe model for one listing representing
  multiple identical rentable items.
- Add quantity fields and overlap/capacity checks only if the selected model
  needs them; preserve current one-listing-as-one-item behavior by default.
- Keep owner UX minimal: creation/update payloads, owner listing text, and
  reservation availability checks.
- Do not add per-item serial tracking, deposits, escrow, or complex inventory
  calendars in this slice.

Completion criteria:

- Migration and backend tests cover default quantity, quantity update,
  overlapping holds up to capacity, and rejection over capacity.
- Bot tests cover owner/listing text and reservation behavior affected by
  quantity.
- Migration, deploy, status, and log checks are completed and recorded.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-geocoding-contract`

## Slice 16: Rental Geocoding Contract

Suggested `/new-go-slug`: `doverabot-rental-geocoding-contract`

Status: planned

Scope:

- Add a narrow, configurable geocoding contract for rental addresses without
  making any provider mandatory.
- Use mocked provider tests; production should degrade cleanly when no provider
  is configured.
- Offer address-to-coordinate suggestions for listing/search only after explicit
  user confirmation.
- Keep map visibility rules unchanged and do not leak private or mistrusted
  listings through geocoding results.

Completion criteria:

- Backend or bot adapter tests cover configured provider success, no-provider
  fallback, ambiguous result prompting, and failed lookup.
- Bot tests cover confirmation before coordinates are stored or used.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-rental-semantic-search-ranking`

## Slice 17: Rental Semantic Search Ranking

Suggested `/new-go-slug`: `doverabot-rental-semantic-search-ranking`

Status: planned

Scope:

- Improve rental search ranking beyond exact text and curated taxonomy while
  keeping trust and visibility rules as hard filters.
- Start with a bounded adapter or PostgreSQL-backed approach that can be tested
  locally; do not make an external vector service the source of truth.
- Preserve equipment taxonomy clarification for ambiguous terms.
- Keep generated frontend bundles out of scope.

Completion criteria:

- Backend tests prove visibility/mistrust filters run before ranking and cannot
  be bypassed by semantic matches.
- Search tests cover taxonomy-only, text fallback, and semantic/ranking-enabled
  cases with deterministic fixtures.
- Runtime code changes are committed, deployed, and logged.

Print after completion, suggested next `/new-go-slug`:
`doverabot-next-decision-refresh`
