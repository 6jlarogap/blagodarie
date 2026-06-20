# Log

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
