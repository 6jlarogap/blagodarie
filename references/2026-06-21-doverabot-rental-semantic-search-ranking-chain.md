# Doverabot Rental Semantic Search Ranking Chain

Date: 2026-06-21
Slug: `doverabot-rental-semantic-search-ranking`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state
Source commit: `8f9fda8`

## Scope

- Improve rental search ranking beyond exact text and curated taxonomy while
  keeping trust and visibility rules as hard filters.
- Start with a bounded adapter or PostgreSQL-backed approach that can be tested
  locally; do not make an external vector service the source of truth.
- Preserve equipment taxonomy clarification for ambiguous terms.
- Keep generated frontend bundles out of scope.

## Implementation

- Reworked `/api/rental/search` so status, visibility, mistrust, trusted-only,
  date, price, and coordinate filters remain hard queryset filters before any
  ranking is applied.
- Added a bounded deterministic ranking pass over up to 200 already-visible
  candidate offers.
- Ranked exact phrase matches, token overlap in title/body/equipment terms,
  curated equipment-type matches, and small local semantic token groups.
- Preserved ambiguous taxonomy clarification behavior: ambiguous-only queries
  still return clarification choices instead of ranked offers.
- Kept frontend bundles out of scope.

## Verification

Source checks:

- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests --settings=app.test_settings --noinput` from `app/` -> 20 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings` from `app/` -> OK, no issues.
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations users --check --dry-run --settings=app.test_settings` from `app/` -> OK, no changes detected; emitted the same local PostgreSQL socket permission warning while checking migration history.
- `python3 -m unittest discover telegram-bot/tests` -> 95 tests OK.
- `python3 -m compileall app/users/views.py app/users/tests.py` -> OK.
- `git diff --check` -> OK.
- `bash scripts/reindex.sh` -> OK; rebuilt local CODE_INDEX pyramid.
- `uv tool run --from graphifyy graphify update .` -> OK; rebuilt AST graph with 4586 nodes, 9122 edges, and 466 communities.

Runtime handoff:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> completed, but
  the rsync plan still included unrelated untracked local state, specifically
  `>f+++++++++ scripts/unblock-django-test-db.sh`.
- Runtime `sync`, `migrate`, and `deploy` were not run for this slice because
  the active wrapper would still sync unrelated untracked local state. The repo
  wrapper exclusion remains blocked by sudo authentication as recorded in
  [2026-06-21-doverabot-rental-proof-dispute-controls-chain.md](2026-06-21-doverabot-rental-proof-dispute-controls-chain.md).
- No schema migration was added in this slice.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-next-decision-refresh`
