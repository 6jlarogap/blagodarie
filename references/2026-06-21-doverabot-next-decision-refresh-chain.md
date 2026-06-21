# Doverabot Next Decision Refresh Chain

Date: 2026-06-21
Status: implemented; runtime deploy not required
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Slug: `doverabot-next-decision-refresh`

## Scope

- Re-read the active Doverabot project note, completed chain references, and
  current source/test state.
- Decide whether the next work should stay on legacy hardening, return to
  rental V1, or move to a new product slice.
- Update the go-next chain and the parent project note so the next `/new go`
  command is concrete again.

## Decision

Choose rental V1 owner-listing management next.

Rationale:

- The recent legacy hardening slices covered the known callback parsing,
  runtime deep-link, stale/auth feedback, command interruption, and mocked
  handler-test backlog.
- The rental core now has listing creation, search, map exposure, reservation
  holds, payment-proof handoff, explicit mistrust checks, and smoke coverage.
- The remaining visible product gap is owner operation: `/rent` still exposes
  create and search, but owners do not have a discoverable path to list, pause,
  resume, archive, or reopen their own rental offers.

Chosen next `/new-go-slug`:
`doverabot-rental-owner-listing-controls`

Planned follow-up after that:
`doverabot-rental-reservation-history-controls`

## Source And Test State Read

- Root and relevant subindexes read: `CODE_INDEX.md`, `telegram-bot/CODE_INDEX.md`,
  `telegram-bot/tests/CODE_INDEX.md`, and `app/users/CODE_INDEX.md`.
- Current last source commit before this refresh: `48e9ba7 doverabot-rental-v1-smoke-observability`.
- Worktree was clean before the refresh edits.
- Bot test surface currently has 71 discovered tests from the previous slice.
- Rental backend tests cover rental offer create/search/map/taxonomy, reservation
  holds, payment-proof checks, and owner/consumer reservation actions.

## Superseded Or Deferred Suggestions

- `doverabot-next-decision-refresh` has now been consumed by this chain.
- Remaining generic legacy-hardening backlog is treated as covered by the
  completed hardening slices unless a new regression is found.
- Rental map frontend/filter UI, reservation history, inventory quantities,
  fake-proof policy, configurable hold duration, geocoding, and vector search
  remain deferred beyond owner listing controls.

## Verification

Checks run:

- `python3 -m unittest discover telegram-bot/tests` -> 71 tests OK; emitted
  the expected test warning about volatile `MemoryStorage`.
- `python3 -m compileall -q telegram-bot` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> OK,
  no issues.
- `bash scripts/reindex.sh` -> OK; rebuilt CODE_INDEX to 122 files, 1480
  symbols, 32 scopes.
- `uv tool run --from graphifyy graphify update .` -> OK; AST graph rebuilt
  with 4408 nodes, 8805 edges, and 440 communities. The tool noted that
  semantic doc refresh uses the separate `/graphify --update` path; this slice
  changed only handoff docs and no runtime code.

## Operational Handoff

- Runtime source and migrations were not changed in this slice; deploy is not
  required.
- Commit source/docs after checks pass with message
  `doverabot-next-decision-refresh`.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-owner-listing-controls`
