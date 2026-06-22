# Blagodarie Maintenance Workspace

This directory is the editable source workspace for the live deployment at
`/srv/blagodarie`.

Secrets and runtime state are intentionally excluded from this workspace:

- `app/app/local_settings.py`
- `telegram-bot/settings_local.py`
- `telegram-bot-api/`
- `venv-app/`
- `app/media/`
- `audit/`
- temp/cache directories

After editing source here, deploy with the root-owned wrapper:

```bash
sudo -n /usr/local/sbin/blagodarie-admin deploy
```

If the wrapper is missing or has changed in this repo, install it once from
the host account:

```bash
sudo bash /home/vdrzd/projects/blagodarie/deploy/install-blagodarie-admin-workflow.sh
```

For a repeatable agent bootstrap that also verifies noninteractive access and
the local helper exclusion:

```bash
sudo bash /home/vdrzd/projects/blagodarie/scripts/enable-agent-deploy-permissions.sh
```

Nginx site configs are tracked under `deploy/nginx/sites-available/`. After
editing them, install only those site configs with:

```bash
sudo -n /usr/local/sbin/blagodarie-admin install-nginx-sites
```

Useful checks:

```bash
sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run
sudo -n /usr/local/sbin/blagodarie-admin check-django
sudo -n /usr/local/sbin/blagodarie-admin nginx-test
sudo -n /usr/local/sbin/blagodarie-admin is-active
sudo -n /usr/local/sbin/blagodarie-admin logs-web 120
sudo -n /usr/local/sbin/blagodarie-admin logs-bot 120
sudo -n /usr/local/sbin/blagodarie-admin install-rental-stt
sudo -n /usr/local/sbin/blagodarie-admin restart-rental-stt
sudo -n /usr/local/sbin/blagodarie-admin logs-rental-stt 120
```

## Chain Success Handoff

For a `/new go` chain or similarly scoped implementation slice, treat success
as an operational handoff:

1. Run relevant source checks.
2. Commit the successful source state with the chain slug in the message.
3. If migrations or runtime code changed, deploy from this workspace with the
   `blagodarie-admin` wrapper.
4. Run migration/deploy/status checks after the commit.
5. Record the result in `log.md` or the chain reference, including exact
   blockers and failed commands when any step cannot run.

Maintainer helper:

```bash
scripts/chain-handoff.sh --new-go-slug CHAIN_SLUG
scripts/chain-handoff.sh --new-go-slug CHAIN_SLUG --runtime --logs
```

The helper runs source checks, commits only already-staged changes with the
mandatory `/new go` slug, and refuses unstaged tracked changes or untracked
non-ignored files. Positional slug arguments are rejected. Use `--runtime` when
migrations or runtime code changed; it then runs `deploy-dry-run`, `sync`,
`migrate`, `deploy`, and `is-active` through the `blagodarie-admin` wrapper.
Record the result in `log.md` or the chain reference after the run.

## Agent Chain Guardrails

Reusable prompt, checklist, recovery, parallelism, branch/worktree, and dirty
worktree rules are captured in
`references/2026-06-22-agent-chain-operational-hardening-chain.md`.

Operational defaults:

1. Resume unfinished chains from the durable chain file, latest commits,
   `log.md`, and current `git status`, not chat memory.
2. Use one serial worker unless write sets, tests/state, and deploy paths are
   all disjoint.
3. Use branch-per-chain or a separate git worktree for long-running or parallel
   work, then merge back to this deployment workspace before deploy.
4. Before broad commit, sync, migrate, or deploy helpers, identify dirty tracked
   and untracked files, mark ownership, and refuse the helper unless unrelated
   files are excluded, cleared by their owner, or explicitly confirmed safe.
5. With unrelated local dirt present, prefer manual staged-only commits for the
   chain's owned files and record the foreign paths left untouched.
