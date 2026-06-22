# Log

## 2026-06-22

- Implemented and deployed `vpn-slice-worker-chain`: added current-server-only
  VPN profiles with weekly subscription token rotation, subscription URL
  serving, sanitized Xray counter import with weekly/monthly rollups, runway
  ledger, opt-in donor highlights, structured fresh-config failure tickets, and
  bot commands `/vpn`, `/fresh`, `/my_usage`, `/vpn_dashboard`, and
  `/connect_friend`. Source commit: `17fa53a`. Checks passed: Python syntax
  compile for changed backend/bot files, `git diff --check`, Django check,
  focused Django `users` tests (29 tests), migration drift check (`No changes
  detected`; history check printed a local PostgreSQL socket permission
  warning), and graphify update. Runtime handoff completed through
  `blagodarie-admin`: dry-run, sync, migration `users.0063_vpn_mvp`, deploy,
  `check-django`, `is-active`, and `status` all completed; nginx/web/bot are
  active. Existing Django `security.W002` clickjacking middleware warning
  remains. Funding copy is scoped to the current prepaid server and does not
  suggest renting a new server.
- Implemented and deployed `doverabot-rental-frontend-media-thumbnails`:
  rental offer/search payloads now expose Telegram-origin media metadata,
  photo thumbnails are proxied server-side through
  `/api/rental/media/<tgdesc_id>/thumbnail/` without exposing the bot token,
  and maintained `/rent/` cards render bounded thumbnails with non-photo
  fallback labels. Source commit: `1d1c14b`. Checks passed:
  focused Django `users` tests (23 tests), Django check, JS syntax check for
  `frontend/rent_map/code.js`, `git diff --check`, reindex, and graphify
  update. Runtime deploy completed through `blagodarie-admin deploy`; the
  existing Django `security.W002` warning remains, nginx syntax was OK,
  nginx/web/bot are active, live smokes returned HTTP 200 for `/rent/`,
  `/rent/code.js`, `/rent/style.css`, and `/api/rental/search/`, and the new
  thumbnail route returned expected HTTP 404 for an invalid media id. Recent
  web/bot log tails showed service restart entries only. Next slug:
  `doverabot-rental-owner-web-controls`.
- Implemented and deployed `doverabot-rental-voice-stt-observability-recovery`:
  owned the previously uncommitted rental bot voice/STT changes, added
  STT-aware rental prompts, opt-in structured debug logging, spoken Russian
  date/address slot extraction, and visible unrecognized-voice feedback; added
  focused mocked tests; committed source as `95283ce`. Checks passed:
  `git diff --check`, focused rental bot tests, full mocked bot discovery
  (97 tests), bot compileall, Django test-settings check, reindex, and graphify
  update. Runtime deploy completed through `blagodarie-admin deploy`; the
  existing Django `security.W002` warning remains, nginx syntax was OK,
  nginx/web/bot are active, and recent web/bot log tails showed service restart
  entries only. The active product next slug remains
  `doverabot-rental-frontend-media-thumbnails`.
- Implemented `agent-chain-orchestration-hardening`,
  `agent-parallel-integrity-rules`, `agent-unfinished-chain-recovery`,
  `agent-worktree-branch-strategy`, and `agent-dirty-worktree-guard` as a
  docs/process hardening chain: added a reusable serial worker prompt template,
  coordinator checklist, parallel-worker integrity rules, durable unfinished
  recovery rules, branch/worktree deployment strategy, and dirty-worktree
  preflight guard. Updated `DEPLOYMENT.md` to link the guardrails. Checks
  passed: `bash scripts/reindex.sh`, graphify incremental update, `git diff
  --check`, shell syntax checks for the handoff/deploy helpers, and
  `python3 -m py_compile scripts/code_index.py`. Runtime deploy not required.
  Existing foreign dirty bot files and untracked
  `scripts/unblock-django-test-db.sh` were left untouched and unstaged.
- Implemented `doverabot-next-decision-refresh`: re-read the saved rental
  frontend redesign chain and current runtime state, confirmed nginx,
  gunicorn, and telegram-bot active with `sudo -n
  /usr/local/sbin/blagodarie-admin status`, and selected
  `doverabot-rental-frontend-mvp` as the active next implementation slice.
  Runtime deploy not required for this docs-only refresh; next slug is
  `doverabot-rental-frontend-mvp`.
- Implemented and deployed `doverabot-rental-frontend-mvp`: added maintained
  no-build static source at `frontend/rent_map/`, served it at `/rent/` with a
  shared `/common/` nginx alias while preserving the legacy map at `/`, and
  moved rental bot map links to `/rent/` without dropping existing rental query
  parameters. Checks passed: JS syntax, focused rental bot tests, full mocked
  bot discovery, compileall, `git diff --check`, reindex, graphify update, and
  nginx syntax/install. Deployment ran through `blagodarie-admin deploy`; the
  existing Django `security.W002` warning remains. Post-deploy `is-active`
  returned active for nginx/web/bot, status showed web and bot restarted, live
  smokes returned HTTP 200 for `/rent/`, `/rent/code.js`, `/common/js/funcs.js`,
  legacy `/`, rental search, and rental map points, and recent web/bot log tails
  showed only service restart entries. Unrelated local tracked bot changes were
  temporarily stashed before deploy and restored afterward; the untracked
  `scripts/unblock-django-test-db.sh` helper remained unstaged.
- Implemented and deployed `doverabot-rental-frontend-live-polish`: improved
  `/rent/` loading, empty, and error states; added a mobile bottom sheet,
  viewport-bound refresh, URL state, and direct `rental_uuid` offer lookup.
  Checks passed: JS syntax, local static HTTP smoke for polished HTML/JS/CSS,
  `git diff --check`, reindex, and graphify update. Browser viewport automation
  was blocked because `require('playwright')` failed and no
  Chromium/Chrome/Firefox binary was present in `PATH`; live HTTP smokes with
  direct `rental_uuid` and viewport-style params returned 200 for `/rent/`,
  `/rent/code.js`, `/rent/style.css`, and rental map points. Static deploy ran
  through `blagodarie-admin deploy-static`, nginx syntax passed, and
  `is-active` returned active for nginx/web/bot. Unrelated local tracked bot
  changes were temporarily stashed before deploy and restored afterward; the
  untracked `scripts/unblock-django-test-db.sh` helper remained unstaged.
- Implemented `doverabot-rental-frontend-followup-decision`: selected
  `doverabot-rental-frontend-media-thumbnails` as the active next slug because
  the maintained `/rent/` frontend has map/list/URL behavior but listing cards
  still lack the already-preserved Telegram offer media. Deferred owner web
  controls, reservation-history web controls, and legacy map cleanup until the
  renter-facing card surface has media parity. Runtime deploy not required for
  this docs-only decision.

## 2026-06-21

- Implemented and deployed `doverabot-rental-runtime-deploy-unblock`: added the
  repeatable `scripts/enable-agent-deploy-permissions.sh` bootstrap and
  documented it, confirmed dry-run no longer includes the unrelated untracked
  `scripts/unblock-django-test-db.sh`, synced source, applied
  `users.0061_rental_payment_proof_rejected_event` and
  `users.0062_rentaloffer_quantity_total`, deployed/restarted web and bot,
  confirmed nginx/web/bot active, and smoked rental search HTTP 200, map points
  HTTP 200, map page HTTP 200, bare offer lookup expected HTTP 404, and
  reservation-history bad-token guard expected HTTP 400. Existing Django
  `security.W002` warning remains; the untracked test-DB helper was not
  deployed.
- Attempted `doverabot-rental-runtime-deploy-unblock`: confirmed
  `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` still includes the
  unrelated untracked `scripts/unblock-django-test-db.sh` helper, while the
  tracked wrapper source already excludes it. Wrapper reinstall is blocked:
  `sudo bash deploy/install-blagodarie-admin-workflow.sh` and the escalated
  rerun both failed with `sudo: A terminal is required to authenticate`.
  Sync/migrate/deploy and live rental smokes were not run; the untracked helper
  was not removed, staged, or deployed.
- Implemented `doverabot-next-decision-refresh` after the saved rental future
  slices: re-read the project note, go-next chain, completed geocoding and
  semantic-ranking references, and source/test state; selected
  `doverabot-rental-runtime-deploy-unblock` as the next active slice because
  accumulated rental runtime source and migrations are committed but not
  deployed while the active wrapper dry-run still includes the unrelated
  untracked `scripts/unblock-django-test-db.sh` helper. Runtime deploy not
  required for this docs-only refresh.
- Source-implemented `doverabot-rental-semantic-search-ranking`: changed
  `/api/rental/search` to apply status/visibility/mistrust/trusted/date/price/
  coordinate filters before a bounded deterministic ranking pass, preserving
  ambiguous equipment clarification while adding taxonomy-only, text fallback,
  and local semantic-token matches; committed source as `8f9fda8`. Rental
  backend tests, full mocked bot discovery, Django check, migration drift check,
  compileall, diff check, reindex, and graphify update passed. Runtime deploy
  remains blocked: `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run`
  still includes `>f+++++++++ scripts/unblock-django-test-db.sh`, so
  sync/migrate/deploy were not run.
- Source-implemented `doverabot-rental-geocoding-contract`: added optional
  `doverabot_rental_geocoding_v1` bot settings and adapter parsing, prompted
  listing/search users with provider suggestions only when configured, and
  applied coordinates to offer creation or bounded search only after explicit
  callback confirmation; focused rental bot tests, full mocked bot discovery,
  Django check, compileall, diff check, reindex, and graphify update passed.
  Runtime deploy remains blocked: `sudo -n /usr/local/sbin/blagodarie-admin
  deploy-dry-run` still includes `>f+++++++++
  scripts/unblock-django-test-db.sh`, so sync/migrate/deploy were not run.
- Source-implemented `doverabot-rental-inventory-quantity-groundwork`: added
  `RentalOffer.quantity_total` defaulting to 1, API create/update validation,
  capacity-aware overlap checks that allow reservations up to listing quantity,
  quantity parsing from owner listing text, and public/owner card quantity
  display for multi-item listings. Full mocked bot discovery, full rental
  backend tests, Django check, and migration drift check passed; migration
  `users.0062_rentaloffer_quantity_total` is committed but not applied because
  runtime deploy remains blocked by the active wrapper/untracked-helper issue.
- Source-implemented `doverabot-rental-map-query-link-polish`: bot map links
  now carry rental UUID/query/equipment/date/price/trusted-only params from
  search, owner listing, and reservation-history contexts; `with_rentals=on`
  and `rental=on` were covered on the shared map-points filter path, including
  private and mistrusted listing hiding. Public read-only rental search and map
  points smokes returned HTTP 200. Generated frontend bundles were not edited;
  runtime deploy remains blocked by the active wrapper/untracked-helper issue.
- Source-implemented `doverabot-rental-voice-search-refinement`: rental search
  parsing now carries date, price ceiling, trusted-only, and map-intent slots
  through the bot FSM/API call; `/api/rental/search` now honors `price_max` and
  `trusted_only` under existing visibility/trust filters; ambiguous equipment
  clarification and result cards remain compatible. Full mocked bot discovery,
  full rental backend tests, Django check, and migration drift check passed;
  runtime deploy remains blocked by the active wrapper/untracked-helper issue.
- Source-implemented `doverabot-rental-voice-listing-clarifications`: rental
  offer voice/text slot extraction now parses dates/availability, accumulates
  partial listing fields in FSM state, prompts for missing item/place/dates/price
  before API creation, and keeps the complete one-message path compatible;
  mocked bot discovery and Django check passed. Runtime deploy remains blocked
  by the active wrapper/untracked-helper issue recorded for
  `doverabot-rental-proof-dispute-controls`.
- Source-implemented `doverabot-rental-hold-duration-config`: replaced the
  rental reservation hold constant with `RENTAL_RESERVATION_HOLD_SECONDS`
  defaulting to 600 seconds, exposed `reservation.hold_seconds` in API
  payloads, and made bot reservation text use that configured value; focused
  backend and mocked bot tests plus full rental/backend checks passed. Runtime
  deploy remains blocked by the active wrapper/untracked-helper issue recorded
  for `doverabot-rental-proof-dispute-controls`.
- Source-implemented `doverabot-rental-proof-dispute-controls`: added owner-only
  payment-proof rejection as a distinct audited event that terminally cancels
  the reservation without writing trust/mistrust state, added owner/requester
  bot text and reject-proof markup, and covered backend plus mocked bot paths;
  committed source as `0a65c6d`. Runtime deploy is blocked: active
  `blagodarie-admin deploy-dry-run` would sync the unrelated untracked
  `scripts/unblock-django-test-db.sh`, the repo wrapper was patched to exclude
  it, but `sudo bash deploy/install-blagodarie-admin-workflow.sh` failed with
  `sudo: A terminal is required to authenticate`; sync/migrate/deploy were not
  run to avoid deploying unrelated local state.
- Extended the Doverabot go-next chain beyond the active proof-dispute slice:
  saved ordered follow-up slugs for hold-duration config, voice listing
  clarifications, voice search refinement, map query/link polish, inventory
  quantity groundwork, geocoding contract, and semantic search ranking, so
  future `/new go` runs can advance without repeating decision-refresh
  investigations after every slice; diff check, reindex, and graphify update
  passed; skipped deploy because only handoff documentation changed.
- Implemented `doverabot-next-decision-refresh` after reservation history:
  re-read the Doverabot project note, go-next chain, completed rental owner
  listing and reservation history references, and current rental map/proof
  source state; marked reservation history consumed; deferred map UI because
  only generated map bundles are present in this workspace; selected
  `doverabot-rental-proof-dispute-controls` as the next active implementation
  slice; bot tests, compileall, Django check, reindex, diff check, and graphify
  update passed; skipped deploy because only handoff documentation changed.
- Implemented and deployed `doverabot-rental-reservation-history-controls`: added bot-authenticated reservation history on `/api/rental/reservation` with requester/owner role filters and open/recent-closed status groups, added `/rent_history` cards with recovered action buttons plus concise event/proof audit text, fixed expired accepted holds moving into closed history, committed source as `3b75b0c`, deployed through the wrapper with no migrations to apply, confirmed nginx/web/bot active, smoked reservation-history token guard HTTP 400 plus rental search and rental map HTTP 200. Focused bot tests and Django source checks passed; DB-backed `manage.py test users` remains blocked by local PostgreSQL peer authentication for user `postgres`.
- Implemented and deployed `doverabot-rental-owner-listing-controls`: added bot-authenticated owner listing on `/api/rental/offer`, `/rent_my` owner cards with pause/resume/archive/public-link/map-link controls, command interruption support for rental commands, and focused backend/mocked bot tests; committed source as `ae72341`; deployed through the wrapper with no migrations to apply; confirmed nginx/web/bot active; public rental search and map smokes returned HTTP 200, and bare rental offer lookup returned expected HTTP 404.
- Implemented `doverabot-next-decision-refresh`: re-read the Doverabot project note, completed chain references, and rental/bot source-test state; marked the prior decision-refresh slug consumed; selected `doverabot-rental-owner-listing-controls` as the next active implementation slice and `doverabot-rental-reservation-history-controls` as its follow-up; skipped deploy because only handoff documentation changed.
- Implemented `doverabot-rental-v1-smoke-observability`: added mocked rental smoke coverage for inline search/date params, successful booking prompt registration plus owner notification, and payment-proof pack forwarding/owner notice/FSM cleanup; documented live-safe and optional write-path curl smoke commands for rental search, map exposure, offer lookup, reservation, proof, and cancel; live read-only smokes returned rental search HTTP 200, rental map points HTTP 200, and expected rental offer lookup HTTP 404; advanced the go-next chain to `doverabot-next-decision-refresh`; full bot discovery now runs 71 tests; skipped deploy because no runtime source changed.
- Added `doverabot-go-next-chain`: an ordered set of `/new go` slices so the latest completed chain suggests `doverabot-offer-sympa-feedback-coverage`, and each planned slice points to the next slug through a decision-refresh handoff.
- Implemented `doverabot-handler-test-harness-split`: extracted the shared mocked aiogram/settings/common test stubs into `telegram-bot/tests/bot_test_harness.py`, split the 68 existing bot tests into domain files for common, profile callbacks, offer/sympathy, relatives, rental, and main storage, regenerated CODE_INDEX/graphify metadata, and skipped deploy because no runtime code or migrations changed.
- Implemented and deployed `doverabot-runtime-deeplink-consistency`: centralized bot start-link generation in `Misc.get_start_deeplink`, routed profile/meet/offer/rental deeplinks through the runtime helper while preserving payload formats, added mocked regressions across common/callback/offer/rental paths for runtime usernames, committed source as `44729d7`, deployed through the wrapper with no migrations to apply, and confirmed nginx/web/bot active with no traceback in recent log tails.
- Implemented and deployed `doverabot-legacy-callback-parser-audit`: audited non-rental callback parsing and duplicate handler names, confirmed no direct non-rental callback-data splits remain outside shared/rental parser helpers, added typed parsers for sympathy common callbacks and meet action callbacks, extended mocked bot coverage to 64 tests, committed source as `2b317dc`, deployed through the wrapper with no migrations to apply, and confirmed nginx/web/bot active with no traceback in recent log tails.
- Implemented and deployed `doverabot-offer-sympa-feedback-coverage`: added visible stale/auth/API feedback across offer geo, offer description/location editing, offer broadcast, offer donation, and reciprocal-sympathy donation paths; added command interruption handling for sympathy donation messages; extended mocked bot coverage to 61 tests including offer/sympathy failure paths and successful offer message delivery; committed source as `8024078`; deployed through the wrapper with no migrations to apply; and confirmed nginx/web/bot active with no new traceback in recent log tails.
- Implemented and deployed `doverabot-profile-edit-state-feedback-finish`: added visible profile-edit message-state feedback for stale FSM data, profile auth failure, and API failure across IOF, meet DOB/description, date/comment/message/user-desc/banking, and thank-bank states; preserved media-pack behavior; added mocked invalid-state/auth/API/command-interruption tests; committed source as `bacb27a`; deployed through the wrapper with no migrations to apply; and confirmed nginx/web/bot active with no new failure lines in recent log tails.
- Implemented and deployed `doverabot-profile-edit-callback-feedback-finish`: added visible stale/auth callback feedback across the remaining parser-backed profile-edit IOF/date/comment/delete/undelete/messaging/archive/user-desc/banking paths, hardened meet edit-back and archive deletion callback exits, fixed comment precheck and delete error-reporting bugs, added mocked regression tests, committed source as `5e33475`, deployed through the wrapper with no migrations to apply, and confirmed nginx/web/bot active with no new traceback in recent log tails.
- Implemented and deployed `doverabot-profile-edit-callback-split-cleanup`: removed remaining direct callback data splits from `handler_callbacks.py`, added stale/auth callback notices around the edited profile/meet/date/attitude paths, fixed the meet gender auth guard's preloaded-state bug, added mocked regression tests, committed source as `ab6dfdf`, deployed through the wrapper with no migrations to apply, and confirmed nginx/web/bot active with no new traceback in recent log tails.
- Implemented and deployed `doverabot-runtime-bot-link-cleanup`: replaced the remaining runtime hard-coded sympathy profile deep link with the shared bot username-aware helper, added a mocked sympathy handoff regression test, committed source as `77ae6db`, deployed through the wrapper with no migrations to apply, and confirmed nginx/web/bot active with no new traceback in recent log tails.
- Implemented and deployed `doverabot-legacy-relatives-media-command-tests`: converted relatives/profile-photo callback failure exits to shared stale/auth alerts, fixed local profile-photo error paths, added mocked tests for relatives callbacks, profile media callbacks, media pack extraction, and non-rental command interruption, committed source as `54bdbbd`, deployed through the wrapper with no migrations to apply, and confirmed nginx/web/bot active with no new traceback in recent log tails.
- Implemented and deployed `doverabot-legacy-callback-cleanup-feedback`: centralized shared callback payload helpers, renamed duplicate legacy callback handlers, added stale/auth alert feedback across offer/sympathy/thank/meet non-rental callback paths, covered parser and offer feedback branches in mocked bot tests, committed source as `2ebc3b3`, deployed through the wrapper with no migrations to apply, confirmed nginx/web/bot active, and smoked rental search plus rental map points with HTTP 200.
- Implemented and deployed `doverabot-rental-callback-payload-feedback`: centralized rental booking/contact/reservation callback payload parsing, added stale/auth callback alerts, covered malformed payloads and auth failure in mocked bot tests, committed source as `ee651ce`, deployed through the wrapper with no migrations to apply, confirmed nginx/web/bot active, and smoked rental search plus rental map points with HTTP 200.
- Implemented `doverabot-rental-durable-fsm-hermes-map-marker-tests`: durable Redis FSM selection for the bot, explicit Organizm/Hermes rental STT helpers, rental map links/markers/filter forwarding, backend rental map assertions, and mocked rental handler tests. DB-backed `manage.py test users` remains blocked by local PostgreSQL peer authentication for user `postgres`.
- Committed and deployed `doverabot-rental-durable-fsm-hermes-map-marker-tests`: source commit `e85a984`, no migrations to apply, nginx/web/bot active, rental search and rental map smoke checks returned HTTP 200, and recent web/bot log tails showed no new traceback after restart.

## 2026-06-20

- Added `doverabot-rental-go-rent-baskets-chain`: saved the `/new go rent` one-session-shot chain for timed rental holds, payment-proof reuse, trust-based exclusions, 10th/system trust-first booking, voice-only listing/search, map UX improvements, and operational handoff.
- Added `doverabot-equipment-rental-trust-flow-plan`: documented the one-public-Doverabot topology, rental roles, trust-aware rental flow, cross-feature boundaries, split-bot criteria, and docs-only scope.

## 2026-06-18

- Added the Doverabot rental-offers architecture reference for the new `/rent` surface.
- Added `doverabot-rental-offers-chain` with child tracks for data model/API, bot voice UX, search/map, trust/privacy, and tests.
- Created the Doverabot revival project note and captured the rental-offers implementation backlog.
- Implemented the initial rental V1 code slice: models/migration, API endpoints, search/map exposure, bot commands, media preservation, contact handoff, and focused backend tests.
- Added next-work baskets for deployment, Telegram message identity, voice-only managed search, multilingual equipment matching, reservation donation policy, and `/new-go-slug`.
- Accepted the one-session-shot next goal: deployment, copied/forwarded offer messages with booking keyboard, English/Russian taxonomy, voice search, and global 10th reservation system-owner payment substitution.
- Implemented and deployed `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`: rental message identity, copied search results with booking keyboard, reservation payment handoff, English/Russian taxonomy seed, configurable rental STT adapter, migration apply, deploy, and API smoke checks.
- Implemented `doverabot-rental-runtime-concierge-owner-consumer-agent`: audited reservation events, owner/consumer reservation action API, Telegram runtime keyboards for accept/payment reported/confirm/cancel, duplicate active-reservation guard, backend tests, and next handoff `doverabot-rental-durable-fsm-hermes-map-marker-tests`.
- Added the chain-success operational rule: successful chains should be checked, committed, migrated/deployed when runtime code or migrations changed, and logged with exact blockers when any step cannot run.
- Committed and deployed `doverabot-rental-runtime-concierge-owner-consumer-agent`: synced source, applied `users.0059_rentalreservationevent`, restarted web/bot, verified services active, and smoked `/api/rental/search`.
- Implemented and deployed `blagodarie-chain-wrapper-commit-migrate-deploy-handoff`: added a maintainer-side chain handoff helper, committed it as `66b8c08`, ran wrapper-backed dry-run/sync/migrate/deploy/status/log checks, and confirmed nginx, web, and bot active.
- Tightened the chain handoff helper so `/new go` slug is mandatory via `--new-go-slug SLUG`; positional slug arguments are rejected.
