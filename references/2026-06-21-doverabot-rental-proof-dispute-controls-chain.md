# Doverabot Rental Proof Dispute Controls Chain

Date: 2026-06-21
Slug: `doverabot-rental-proof-dispute-controls`
Status: source implemented; runtime deploy blocked by wrapper/untracked-file state

## Scope

- Add an owner-only reservation action for unacceptable or fake payment proof
  after a requester submits proof.
- Record a distinct audited event so `/rent_history` can distinguish proof
  disputes from generic cancellations.
- Release the reserved date interval by moving the reservation to a terminal
  state, without creating mistrust or reputation penalties.
- Update owner/requester bot text and action markup so the owner can reject
  proof and users understand trust/mistrust remains a separate profile action.

## Implementation

- Added `payment_proof_rejected` as a rental reservation event type.
- Added owner-only backend action handling that moves a
  `payment_proof_submitted` reservation to terminal `cancelled` status.
- Added owner bot markup for `Отклонить чек` and requester/owner notification
  text explaining that trust and mistrust are not changed automatically.
- Added backend coverage for requester denial, owner authorization, event
  history, terminal status release, and absence of `CurrentState` writes.
- Added mocked bot coverage for owner markup, callback handling, and requester
  notification text.
- Added a narrow deploy wrapper source exclusion for the known local
  `scripts/unblock-django-test-db.sh` helper after dry-run showed the active
  wrapper would otherwise sync it.

## Verification

Source checks:

- `PYTHONPATH=telegram-bot/tests python3 -m unittest telegram-bot/tests/test_handler_rental.py` -> 21 tests OK.
- `PYTHONPATH=telegram-bot/tests python3 -m unittest discover telegram-bot/tests` -> 79 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests.test_owner_can_reject_payment_proof_as_audited_terminal_dispute --settings=app.test_settings --noinput` from `app/` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests --settings=app.test_settings --noinput` from `app/` -> 12 tests OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check --settings=app.test_settings` from `app/` -> OK, no issues.
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations users --check --dry-run --settings=app.test_settings` from `app/` -> OK, no changes detected; emitted a local PostgreSQL socket permission warning while checking migration history.
- `python3 -m compileall telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py` -> OK.
- `bash scripts/reindex.sh` -> OK; rebuilt local CODE_INDEX pyramid.
- `git diff --check` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK; rebuilt AST graph with 4487 nodes, 8951 edges, and 458 communities.
- `bash -n deploy/bin/blagodarie-admin` -> OK.

Commit:

- `git commit -m "doverabot-rental-proof-dispute-controls"` -> `0a65c6d`.

Runtime handoff:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK, but showed
  the active wrapper would sync unrelated untracked local state, including
  `>f+++++++++ scripts/unblock-django-test-db.sh`.
- `sudo bash deploy/install-blagodarie-admin-workflow.sh` -> blocked:
  `sudo: A terminal is required to authenticate`.
- Re-running the same install command with escalation produced the same sudo
  authentication blocker.
- Non-wrapper sudo probes such as `sudo -n true` were blocked by the sandbox
  `no new privileges` flag.
- `sync`, `migrate`, and `deploy` were not run because the active wrapper would
  deploy the unrelated untracked DB helper. Later source slices can continue;
  runtime deployment remains blocked until the wrapper exclusion is installed
  or the local untracked-file state is otherwise resolved by the maintainer.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-hold-duration-config`
