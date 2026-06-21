# Log

## 2026-06-21

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
