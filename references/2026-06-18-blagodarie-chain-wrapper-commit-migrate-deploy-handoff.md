# Blagodarie Chain Wrapper Commit Migrate Deploy Handoff

Date: 2026-06-18
Status: implemented, committed, and deployed
Started `/new-go-slug`: `blagodarie-chain-wrapper-commit-migrate-deploy-handoff`

## Scope

Make the `/new go` chain success handoff repeatable without moving git
operations into the root-owned deployment wrapper.

Implemented:

- Added `scripts/chain-handoff.sh` as a maintainer-side helper.
- Kept commit behavior conservative: only already-staged changes are committed.
- Added explicit runtime mode for the deploy wrapper sequence:
  `deploy-dry-run`, `sync`, `migrate`, `deploy`, and `is-active`.
- Documented the helper in `DEPLOYMENT.md`.

## Verification

Passed:

- `bash -n scripts/chain-handoff.sh`
- `bash -n deploy/bin/blagodarie-admin`
- `bash -n deploy/install-blagodarie-admin-workflow.sh`
- `bash -n scripts/reindex.sh`
- `python3 -m py_compile scripts/code_index.py`
- `scripts/chain-handoff.sh blagodarie-chain-wrapper-commit-migrate-deploy-handoff`
  -> committed `66b8c08`
- `scripts/chain-handoff.sh blagodarie-chain-wrapper-commit-migrate-deploy-handoff --runtime --logs --no-commit`
  -> ran `deploy-dry-run`, `sync`, `migrate`, `deploy`, `is-active`,
  `logs-web 80`, and `logs-bot 80`

Runtime results:

- Django deploy check completed with the pre-existing `security.W002`
  clickjacking middleware warning.
- Migration command completed with no migrations to apply.
- Deploy restarted nginx, web, and bot successfully.
- `is-active` returned active for nginx, web, and bot.
- Recent web/bot log windows still include old June 16 permission errors, but
  the checked June 18 18:06 restart entries show successful service restarts
  and no new traceback after this deploy in the displayed tail.

Sandbox note:

- The first sandboxed helper run failed at
  `git commit -m blagodarie-chain-wrapper-commit-migrate-deploy-handoff` with
  `fatal: Unable to create '.git/index.lock': Read-only file system`; rerunning
  the same helper with approval completed the commit.
