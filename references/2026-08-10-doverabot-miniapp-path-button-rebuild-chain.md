# Doverabot Mini App Path Button Rebuild Chain

Date: 2026-08-10
Status: ready
Active slug: `doverabot-miniapp-launcher-unification`
Next slug: `doverabot-schema-path-button-rebuild`

## Decision

Do not revert the recent graph/Mini App series wholesale. The reset-view,
private Mini App authentication, group Main Mini App routing, cache
revalidation, and rendering fixes are useful and already deployed. Replace
only the failed own-profile anchoring behavior and consolidate remaining
Schema/Род/Карта launchers through the existing helpers.

Use one serial Luna worker because both slices touch the Telegram launch
contract and the shared graph frontend.

## Slice 1: Mini App Launcher Unification

Slug: `doverabot-miniapp-launcher-unification`
Status: pending
Next: `doverabot-schema-path-button-rebuild`

Scope:

- Trace every Doverabot button labelled or serving `Схема доверия`, `Схема`,
  `Род`, or `Карта`, including direct cards, forwarded-message cards,
  post-operation cards, commands, group pins, sympathy/Meetgame, and video or
  poll graph/map surfaces.
- Reuse `Misc.make_launch_button` for private-chat Mini App buttons and
  `Misc.make_group_launch_button`/Main Mini App links where Telegram does not
  permit inline `web_app` buttons.
- Make private person cards Mini App-first by default so callers cannot silently
  fall back to browser `login_url`; keep a deliberate fallback only where the
  Telegram surface cannot launch a Mini App.
- Preserve target query parameters and viewer identity. Add one focused
  forwarded-message regression plus representative Schema/Род/Карта tests.

Out of scope:

- New launcher abstractions, new auth protocols, backend schema changes, and
  unrelated `Продолжить` or external links.

Complete when:

- No eligible private Schema/Род/Карта constructor uses `login_url`.
- Group/channel launchers use the existing Main Mini App route and still open.
- Focused bot tests and compile checks pass; source is committed, deployed,
  checked, and recorded here before the next slice.

## Slice 2: Schema Path Button Rebuild

Slug: `doverabot-schema-path-button-rebuild`
Status: pending
Next: none

Scope:

- Remove the non-working own-profile pin/anchor behavior introduced by
  `ded6bba`; do not revert the whole commit or later Mini App/auth fixes.
- Keep the second top-right control, but make it open the existing
  `user_trust_path=<viewer uuid>,<viewed profile uuid>` view.
- Reuse `/api/profile_trust` and its existing `find_trust_path_shortest`
  behavior, which returns the union of all shortest trust/acquaintance paths.
- Show the control only on another person's `user_trusts` Schema when both
  endpoints are known and different. Give it a truthful Russian title/label.
- Delete obsolete anchor-only code instead of adding another graph algorithm.
- Add one small runnable frontend contract covering visibility and URL
  construction; retain reset-view and Род behavior.

Out of scope:

- Enumerating every possible cyclic path, a new pathfinding algorithm, backend
  changes, or in-place edge animation. The existing all-shortest-path view is
  the bounded useful interpretation of “all available paths.”

Complete when:

- The second button visibly navigates to the viewer-to-viewed shortest-path
  graph in browser and Mini App entry modes.
- Obsolete pinning code is gone, focused frontend tests/build pass, generated
  dist changes are limited to the required build, and the slice is committed,
  deployed, checked, and recorded here and in `log.md`.

## Worker Rules

- Read `AGENTS.md`, root and nearest `CODE_INDEX.md`, `DEPLOYMENT.md`, and this
  file before edits; run `graphify query` before source reads.
- Preserve others' changes, stage only worker-owned files, and never expose
  secrets or private Telegram data.
- Run slices serially. For each slice: inspect status, implement the smallest
  shared fix, run focused checks, update Graphify, commit with the slug, deploy
  runtime changes through `blagodarie-admin`, verify services/logs, update this
  ledger and `log.md`, then continue.
- Stop and report the exact blocker if a required check, commit, permission, or
  deploy step fails; do not paper over failures or revert unrelated work.

## Final Handoff

Report completed slugs, commit hashes, deploy status, checks, blockers, changed
files, and the next active slug (or `none`).
