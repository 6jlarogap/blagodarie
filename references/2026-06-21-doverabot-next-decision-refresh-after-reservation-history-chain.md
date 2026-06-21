# Doverabot Next Decision Refresh After Reservation History Chain

Date: 2026-06-21
Status: implemented; runtime deploy not required
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Slug: `doverabot-next-decision-refresh`

## Scope

- Re-read the active Doverabot project note, current go-next chain, completed
  rental owner-listing and reservation-history references, and source/test state.
- Decide the next small implementation slice after owner listing and reservation
  history are complete.
- Update the go-next chain and parent project note so the next `/new go`
  command is concrete again.

## Decision

Choose rental proof-dispute controls next.

Rationale:

- Owner listing management and reservation history are now implemented and
  deployed, so owners and requesters can recover live reservation controls from
  `/rent_my` and `/rent_history`.
- Backend rental map filtering and marker payloads already exist and are covered
  by tests, while this workspace only contains generated map UI bundles under
  `frontend/*/dist/`; editing those bundles is explicitly avoided unless a
  deployment slice requires generated output.
- The remaining source-owned product gap is fake or unacceptable payment proof:
  reservation proof is stored, forwarded, and auditable, but owners only have
  generic confirm/cancel controls and no explicit proof-dispute event.

Chosen next `/new-go-slug`:
`doverabot-rental-proof-dispute-controls`

Planned follow-up after that:
`doverabot-next-decision-refresh`

## Source And Test State Read

- Graphify queries were run for the active chain, rental map/frontend state, and
  reservation proof state machine before editing.
- Root and relevant subindexes read: `CODE_INDEX.md`, `references/CODE_INDEX.md`,
  `projects/CODE_INDEX.md`, `frontend/CODE_INDEX.md`, `app/users/CODE_INDEX.md`,
  `telegram-bot/CODE_INDEX.md`, and `telegram-bot/tests/CODE_INDEX.md`.
- Current last commit before this refresh: `d62e80e doverabot-rental-reservation-history-controls reference`.
- The tracked worktree was clean before this refresh; untracked
  `scripts/unblock-django-test-db.sh` was present and left untouched.
- Current backend rental tests cover owner listing, rental map marker/filter
  payloads, timed holds, mistrust checks, payment proof, reservation actions,
  and reservation history.
- Current mocked rental bot tests cover `/rent_my`, `/rent_history`, owner
  listing controls, callback stale/auth handling, booking notification, and
  payment-proof forwarding.

## Superseded Or Deferred Suggestions

- `doverabot-rental-reservation-history-controls` has now been consumed by the
  completed reservation-history chain.
- Rental map/frontend filter UI remains deferred until editable frontend source
  is available or a generated-bundle deployment slice is explicitly accepted.
- Inventory quantities, configurable hold duration, geocoding, vector search,
  and auto-mistrust policy remain deferred beyond proof-dispute controls.

## Next Slice Scope

`doverabot-rental-proof-dispute-controls` should stay narrow:

- Add an owner-only proof-dispute/reject action for reservations after payment
  proof is submitted.
- Record an explicit audited event with note/payload so history distinguishes
  a generic cancellation from unacceptable or fake proof.
- Release the date interval by moving the reservation to a terminal state, but
  do not auto-create mistrust; instead make the bot text tell involved users
  that trust/mistrust remains a separate profile action.
- Add backend and mocked bot tests for owner authorization, requester denial,
  event history, terminal status, owner markup, and notification text.

Out of scope:

- escrow or in-bot payment verification;
- moderation dashboards;
- automatic mistrust or reputation penalties;
- inventory quantity support.

## Verification

Checks run:

- `python3 -m unittest discover telegram-bot/tests` -> 77 tests OK; emitted
  the expected volatile `MemoryStorage` warning.
- `python3 -m compileall -q telegram-bot` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> OK,
  no issues.
- `bash scripts/reindex.sh` -> OK; rebuilt local ignored `CODE_INDEX.md`
  navigation to 126 files, 1537 symbols, and 32 scopes.
- `git diff --check` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK; AST graph rebuilt
  with 4475 nodes, 8937 edges, and 441 communities. The tool noted that
  semantic doc refresh uses the separate `/graphify --update` path; this slice
  changed only handoff docs and no runtime code.

## Operational Handoff

- Runtime source and migrations are not changed in this slice; deploy is not
  required.
- Commit source/docs after checks pass with message
  `doverabot-next-decision-refresh`.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-proof-dispute-controls`
