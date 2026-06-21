# Doverabot Rental Runtime Deploy Unblock Chain

Date: 2026-06-21
Status: blocked by sudo authentication before wrapper reinstall
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Slug: `doverabot-rental-runtime-deploy-unblock`

## Scope

- Resolve the operational deploy blocker without removing, staging, or deploying
  the unrelated untracked `scripts/unblock-django-test-db.sh` helper.
- Activate the repo wrapper exclusion so deploy dry-run no longer syncs that
  helper.
- Sync, migrate, deploy, and status-check the accumulated rental runtime source
  once the wrapper plan is clean.
- Smoke rental search, map exposure, reservation/history controls, and migration
  state after deploy.

## Attempted Unblock

- Graphify query was run for the rental deploy-unblock slug before operational
  work.
- Read `CODE_INDEX.md`, `DEPLOYMENT.md`, the Doverabot project note, the
  go-next chain, `deploy/bin/blagodarie-admin`,
  `deploy/install-blagodarie-admin-workflow.sh`, and
  `scripts/chain-handoff.sh`.
- Worktree state before the attempt had no tracked changes and one unrelated
  untracked helper: `scripts/unblock-django-test-db.sh`.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` succeeded but still
  included `>f+++++++++ scripts/unblock-django-test-db.sh`, confirming the
  installed wrapper is stale.
- The tracked wrapper source already contains the intended exclusion:
  `--exclude '/scripts/unblock-django-test-db.sh'`.
- `sudo bash deploy/install-blagodarie-admin-workflow.sh` failed with:
  `sudo: A terminal is required to authenticate`.
- Escalated rerun of
  `sudo bash deploy/install-blagodarie-admin-workflow.sh` failed with the same
  sudo authentication error.

## Result

Runtime deploy remains blocked. I did not run `sync`, `migrate`, `deploy`, or
post-deploy rental smokes because the dry-run still includes unrelated untracked
local state.

No product code changed. The untracked helper was not removed, staged, or
deployed by this attempt.

## Next Step

Run the wrapper installer from an authenticated privileged shell:

```bash
sudo bash deploy/install-blagodarie-admin-workflow.sh
```

Then rerun `doverabot-rental-runtime-deploy-unblock` so dry-run, sync, migrate,
deploy, status checks, and live rental smokes can complete.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-rental-runtime-deploy-unblock`
