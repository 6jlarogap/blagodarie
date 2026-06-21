# Doverabot Next Decision Refresh After Rental Future Slices Chain

Date: 2026-06-21
Status: implemented; runtime deploy not required
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Slug: `doverabot-next-decision-refresh`

## Scope

- Re-read the active Doverabot project note, current go-next chain, completed
  rental future-slice references, and source/test state.
- Decide the next small implementation slice after the saved rental sequence is
  source-complete.
- Update the go-next chain and parent project note so the next `/new go`
  command is concrete again.

## Decision

Choose rental runtime deploy unblock next.

Rationale:

- The saved rental source sequence is complete through proof-dispute controls,
  configurable hold duration, voice listing/search clarifications, map link
  polish, inventory quantity groundwork, geocoding, and semantic search ranking.
- Runtime deploy has been blocked since the proof-dispute slice because the
  active wrapper dry-run still includes the unrelated untracked
  `scripts/unblock-django-test-db.sh` helper, and installing the repo wrapper
  exclusion is blocked by sudo authentication.
- Migrations `users.0061_rental_payment_proof_rejected_event` and
  `users.0062_rentaloffer_quantity_total` are committed in source but not
  applied at runtime.
- Adding more product code before the deployed runtime catches up would make
  the operational gap larger and weaken live feedback.

Chosen next `/new-go-slug`:
`doverabot-rental-runtime-deploy-unblock`

Planned follow-up after that:
`doverabot-next-decision-refresh`

## Source And Test State Read

- Graphify query was run for this decision refresh before editing.
- Root and relevant subindexes read earlier in the saved sequence:
  `CODE_INDEX.md`, `references/CODE_INDEX.md`, `projects/CODE_INDEX.md`,
  `app/users/CODE_INDEX.md`, `telegram-bot/CODE_INDEX.md`, and
  `telegram-bot/tests/CODE_INDEX.md`.
- Current completed source commits include:
  - `3bb272b doverabot-rental-geocoding-contract`
  - `24ca587 doverabot-rental-geocoding-contract handoff`
  - `8f9fda8 doverabot-rental-semantic-search-ranking`
  - `5006e7b doverabot-rental-semantic-search-ranking handoff`
- The tracked worktree was clean before this refresh; untracked
  `scripts/unblock-django-test-db.sh` was present and left untouched.
- Current backend rental tests cover proof rejection, hold duration, voice/search
  parameter filtering, map filtering, inventory quantity capacity, geocoding
  contract behavior through bot tests, and semantic search ranking.
- Current mocked bot discovery surface is 95 tests.

## Superseded Or Deferred Suggestions

- The saved slugs from `doverabot-rental-proof-dispute-controls` through
  `doverabot-rental-semantic-search-ranking` have now been consumed.
- Runtime deployment is now the highest-priority slice because source contains
  backend migrations and runtime bot/backend changes that are not live.
- Further product work such as escrow, richer conflict tracking, generated map
  UI changes, deposits, or moderation dashboards remains deferred until runtime
  deployment is unblocked and smoked.

## Next Slice Scope

`doverabot-rental-runtime-deploy-unblock` should stay operational:

- Re-run the wrapper dry-run and confirm the exact rsync blocker.
- Install or otherwise activate the repo wrapper exclusion for
  `scripts/unblock-django-test-db.sh` without deleting or staging that helper.
- Sync, migrate, deploy, and run status checks through the `blagodarie-admin`
  wrapper once the exclusion is active.
- Apply pending rental migrations and smoke the rental search, map, booking, and
  history/control surfaces after deploy.
- If sudo/auth or environment state still blocks the wrapper update or deploy,
  record the exact failed command and stop without adding new product code.

Out of scope:

- removing unrelated untracked local files;
- unrelated refactors;
- new rental product behavior beyond deployment unblock and smokes.

## Verification

Checks run:

- `python3 -m unittest discover telegram-bot/tests` -> 95 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings` from `app/` -> OK, no issues.
- `python3 -m compileall -q telegram-bot app/users/views.py app/users/tests.py` -> OK.
- `bash scripts/reindex.sh` -> OK; rebuilt local CODE_INDEX pyramid.
- `git diff --check` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK; AST graph rebuilt
  with 4597 nodes, 9134 edges, and 451 communities.

## Operational Handoff

- Runtime source and migrations are not changed in this decision-refresh slice;
  deploy is not required.
- Commit docs after checks pass with message `doverabot-next-decision-refresh`.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-runtime-deploy-unblock`
