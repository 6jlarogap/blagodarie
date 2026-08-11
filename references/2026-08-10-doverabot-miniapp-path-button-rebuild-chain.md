# Doverabot Mini App Path Button Rebuild Chain

Date: 2026-08-10
Status: completed
Active slug: none
Next slug: none

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
Status: completed
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

Handoff: commit `742e010`; private Schema/Род/Карта launchers now default to
Mini App buttons, forwarded profile cards retain their target and viewer query
parameters, and group pins continue using Main Mini App startapp URLs. Focused
bot tests (`22`) and Python compile checks passed; Graphify updated; deploy
completed with Django warning `security.W002`, nginx syntax passed, and all
services reported active.

## Slice 2: Schema Path Button Rebuild

Slug: `doverabot-schema-path-button-rebuild`
Status: completed
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

Handoff: commit `1d9218f`; removed the own-profile pin/anchor module and made
the second control navigate to `user_trust_path=<viewer uuid>,<root uuid>` only
when both UUIDs exist and differ. The browser renders the server-returned
`/api/profile_trust` result; server-side `find_trust_path_shortest` remains the
authoritative visibility-filtered union of all shortest paths, not a client BFS
or enumeration of cyclic paths. Frontend tests (`6`), production build,
generated-bundle `node --check`, Graphify update, deploy, active services,
nginx syntax, and public HTML smoke all passed; deploy emitted only existing
`security.W002`.

## Slice 4: All Trust Paths and Fixed Viewer

Slug: `doverabot-schema-all-paths-fixed-viewer`
Status: completed
Next: none

Scope:

- Highlight every loaded directed simple `a`/`t` route to the Schema root,
  including longer alternatives while excluding cycles and dead branches.
- Keep the authenticated viewer node bottom-centered through pan/zoom/rotate;
  preserve graph link endpoints and use thinner highlighted lines.
- Keep the route icon and Russian title/aria label truthful and accessible.

Handoff: commit `7aacf19`; frontend tests (`7`), production build, built asset
check, diff checks, and Graphify update passed. Deploy-dry-run and wrapper
deploy passed; Django reported only existing `security.W002`, nginx syntax
passed, all four services are active, and requested web/bot logs completed.
Public HTML contains `Подсветить все пути доверия`, icon `↝`, and bundle
`index-DDCO1iQ9.js`; the bundle returns HTTP 200. Documentation-only result
is recorded in this follow-up commit.

## Slice 5: Route Toggle and Viewer Presence

Slug: `doverabot-schema-route-toggle-viewer-presence`
Status: completed
Next: none

Scope:

- Make the all-path control a toggle that releases the anchored viewer and
  clears the sequential highlight on the second press or reset.
- Use the native graph render/link lifecycle during controls changes without
  rebuilding link meshes or reheating the simulation on every pan/zoom.
- Ensure paginated Schema responses include a disconnected Token-authenticated
  viewer without leaking that viewer through shared URL caching.

Result/checks: source and frontend contract updated; frontend tests (`7/7`),
production build, generated-bundle syntax check, diff check, and Graphify
update passed. The targeted PostgreSQL-backed regression passed when rerun by
the parent worker. Deploy, public smoke, and push remain pending.

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

## Slice 3: Visible Schema Path Highlight

Slug: `doverabot-schema-visible-path-highlight`
Status: completed
Depends on: completed Slice 2 at `1d9218f`
Next: none

Scope:

- Keep the completed Mini App launcher unification from `742e010`.
- Replace the second button's `user_trust_path` navigation/API round-trip with
  in-place highlighting over the `data.nodes` and `data.links` already returned
  by `/api/profile_graph` for the current Schema.
- Follow directed trust/acquaintance edges (`t`/`a`) from the viewing user to
  the viewed root. Compute the union of all shortest paths in the loaded graph;
  do not enumerate cyclic or longer paths.
- On one button press, reveal the path edges in order in the existing graph.
  Keep the existing reset button and make it clear the highlight.
- Hide or disable the path button when the viewer/root is absent, identical, or
  disconnected inside the loaded graph. Keep a truthful Russian accessible
  label.
- Reuse the existing graph renderer and its link color/width callbacks. Replace
  the small `trust-path-button.js` helper rather than adding another module or
  backend endpoint.

Out of scope:

- Searching through unloaded database profiles, calling `/api/profile_trust`,
  changing Django/PostgreSQL pathfinding, enumerating all simple paths, or
  changing which nodes `/api/profile_graph` returns.

Complete when:

- Clicking the second button causes no navigation and no API request.
- All loaded shortest viewer-to-root trust/acquaintance path edges are visibly
  highlighted in place, reset clears them, and no-path state is handled.
- One focused helper test covers direct, multiple-shortest, directed, cyclic,
  disconnected, and same-endpoint cases; frontend tests/build and public
  Mini App smoke pass.
- Commit, deploy, service/log checks, and handoff updates are complete.

Handoff: commit `5f763f0`; the existing Schema control now computes the union
of loaded directed shortest `t`/`a` paths in the browser, reveals their links
in breadth order through the existing color/width callbacks, and clears the
highlight on reset. It makes no path navigation or API request and stays hidden
for missing, identical, or disconnected endpoints. Frontend tests (`6`), the
production build, generated-bundle `node --check`, diff checks, and Graphify
update passed. Wrapper deploy, Django and nginx checks, all four service checks,
recent web/bot logs, public HTML markers, and the public hashed bundle (`200`)
passed; Django emitted only the existing `security.W002` warning.

## Final Handoff

Completed slugs: `doverabot-miniapp-launcher-unification`,
`doverabot-schema-path-button-rebuild`,
`doverabot-schema-visible-path-highlight`,
`doverabot-schema-all-paths-fixed-viewer`,
`doverabot-schema-route-toggle-viewer-presence`. Slice 4 source commit:
`7aacf19`;
the documentation follow-up records deploy completion, checks, and changed
files; Slice 5 source remains uncommitted pending deploy/public verification;
next active slug: `none`.
