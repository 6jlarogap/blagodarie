# Doverabot Rental Frontend Redesign Chain

Date: 2026-06-22
Status: implemented; active next slug `doverabot-rental-owner-web-controls`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)

Slug queue:

1. `doverabot-next-decision-refresh`
2. `doverabot-rental-frontend-mvp`
3. `doverabot-rental-frontend-live-polish`
4. `doverabot-rental-frontend-followup-decision`

## Chain Purpose

Replace rental map patching with a maintained rental-first static frontend at
`https://map.doverabot.ru/rent/` while keeping the legacy map at
`https://map.doverabot.ru/` intact. Run the chain with one serial worker because
the slices touch shared frontend source, bot links, nginx routing, deployment
notes, and smoke checks.

## Slice 1: Next Decision Refresh

Slug: `doverabot-next-decision-refresh`
Status: implemented
Next slug: `doverabot-rental-frontend-mvp`

Scope:

- Re-read current production/runtime state and this saved frontend-redesign
  chain.
- Select `doverabot-rental-frontend-mvp` as the next implementation slug.
- Update project/go-next notes only.

Out of scope:

- Source frontend, bot, backend, nginx, or deployment changes.

Completion criteria:

- The Doverabot project note names the rental frontend MVP as the active next
  implementation slice.
- The go-next chain records the rental frontend redesign as the selected
  candidate chain.
- The next slug to print is `doverabot-rental-frontend-mvp`.

## Slice 2: Rental Frontend MVP

Slug: `doverabot-rental-frontend-mvp`
Status: implemented
Next slug: `doverabot-rental-frontend-live-polish`

Scope:

- Add maintained static source under `frontend/rent_map/`.
- Serve it at `https://map.doverabot.ru/rent/`.
- Keep `https://map.doverabot.ru/` legacy map intact.
- Implement responsive filters, map, listing cards, selected marker/card sync,
  and Telegram booking/contact links.
- Update rental bot map links to `/rent/`.

Out of scope:

- Generated-bundle patching under `frontend/*/dist/`.
- Owner dashboard, web booking, escrow/deposits, or reservation-history web
  controls.

Completion criteria:

- `/rent/` loads a rental-first static frontend from maintained source.
- Search/filter parameters are reflected in map/listing requests.
- Selecting a marker selects the corresponding listing card and vice versa.
- Telegram links open existing rental start/contact paths.
- Existing `map.doverabot.ru/` behavior remains routed to the legacy map.
- Bot rental map links point at `/rent/`.
- Relevant bot tests, frontend smoke checks, nginx test if config changed,
  source checks, reindex, graph update, commit, deploy, and handoff logging are
  complete or exact blockers are recorded.

## Slice 3: Rental Frontend Live Polish

Slug: `doverabot-rental-frontend-live-polish`
Status: implemented
Next slug: `doverabot-rental-frontend-followup-decision`

Scope:

- Improve loading, empty, and error states.
- Add a mobile bottom sheet.
- Add viewport refresh.
- Add URL state.
- Support direct `rental_uuid` behavior.
- Add desktop/mobile smoke checks.

Out of scope:

- Owner dashboard.
- Web booking.
- Reservation-history web controls.

Completion criteria:

- `/rent/` behaves cleanly on desktop and mobile viewports.
- Filter and selected-offer state are preserved in the URL.
- Direct `rental_uuid` URLs select and reveal the matching offer when visible.
- Manual or automated desktop/mobile smokes are recorded.
- Relevant checks, reindex, graph update, commit, deploy, and handoff logging
  are complete or exact blockers are recorded.

## Slice 4: Rental Frontend Follow-Up Decision

Slug: `doverabot-rental-frontend-followup-decision`
Status: implemented
Next slug: `doverabot-rental-frontend-media-thumbnails`

Scope:

- Decide whether the next slice is media thumbnails, owner web controls,
  reservation-history web controls, or cleanup of the old rental map patch.
- Update this chain and the project notes with the next slug.

Out of scope:

- Implementing the selected follow-up slice.

Completion criteria:

- The chain/project notes name the selected next slug and why.
- The active next `/new-go-slug` is visible from the parent project note.
- Any deferred candidates are recorded.

## Follow-Up Decision

Selected next slug: `doverabot-rental-frontend-media-thumbnails` (implemented).

Reason: the new `/rent/` frontend now has maintained source, map/list sync,
URL state, and direct offer selection, but listing cards still cannot show the
Telegram-origin offer media already preserved by the rental backend. Media
thumbnails are the smallest user-visible next step and improve renter confidence
without adding owner dashboard or reservation-history web control scope.

Deferred candidates:

- `doverabot-rental-owner-web-controls`: selected next after media thumbnails;
  it introduces a new authenticated owner-management surface.
- `doverabot-rental-reservation-history-web-controls`: useful later, but it
  expands into role-aware reservation actions and audit UX.
- `doverabot-rental-legacy-map-cleanup`: defer until `/rent/` has media parity
  and enough live use to confirm the legacy map no longer needs rental affordances.

## Media Thumbnail Follow-Up

Slug: `doverabot-rental-frontend-media-thumbnails`
Status: implemented
Next slug: `doverabot-rental-owner-web-controls`

Outcome:

- Rental offer/search payloads now include a `media` array derived from stored
  Telegram description packs.
- Telegram photo `file_id` values are rendered through
  `/api/rental/media/<tgdesc_id>/thumbnail/`, which fetches and thumbnails media
  server-side instead of exposing the bot token to the browser.
- Maintained `/rent/` listing cards render bounded media thumbnails and fall
  back cleanly for non-photo media.

## Run Strategy

Use one serial worker through `sliced-chain-worker`, not parallel workers. The
worker must process the slug queue in order, preserve compact handoffs between
slices, and stop if an earlier slice blocks a later dependent slice.

Only consider extending the skill after this chain runs if it shows a repeated
gap, such as needing a reusable "write chain file from proposed plan" template
or a standard worker prompt generator.

## Verification Requirements

Before saving/running:

- Read `CODE_INDEX.md`, relevant subindexes, and use graphify query as repo
  instructions require.

During implementation slices:

- Bot tests for rental map-link changes.
- Frontend smoke with desktop/mobile viewport checks.
- Django check when backend/config touched.
- Nginx test when route config changes.
- `git diff --check`, reindex, and `graphify update .`.
- Commit each successful slice with its slug.
- Deploy runtime/static changes through `blagodarie-admin` and record results
  in this chain or `log.md`.
