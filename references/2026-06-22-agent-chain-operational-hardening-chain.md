# Agent Chain Operational Hardening Chain

Date: 2026-06-22
Status: implemented; runtime deploy not required
Slug queue:

1. `agent-chain-orchestration-hardening`
2. `agent-parallel-integrity-rules`
3. `agent-unfinished-chain-recovery`
4. `agent-worktree-branch-strategy`
5. `agent-dirty-worktree-guard`

## Purpose

Make `/new go` and similarly scoped agent chains repeatable when work spans
multiple slices, commits, checks, and optional deployment. The durable source of
truth is this chain reference plus `log.md`, commit history, and the current
worktree state. Chat memory is only advisory.

## Slice 1: Agent Chain Orchestration Hardening

Slug: `agent-chain-orchestration-hardening`

Status: implemented.

Reusable serial worker prompt template:

```text
You are running a saved /new go chain in /home/vdrzd/projects/blagodarie.

Slug queue, in order:
1. SLUG_1
2. SLUG_2
3. SLUG_N

Authoritative durable chain file:
REFERENCES_CHAIN_FILE

Before edits:
- Read AGENTS.md, CODE_INDEX.md, the nearest subindex for the area edited,
  DEPLOYMENT.md, log.md, the durable chain file, and any latest completed
  chain handoff it references.
- Run graphify query for the chain goal when graphify-out/graph.json exists.
- Inspect `git status --short`, `git log --oneline -n 5`, and untracked files.
- Mark file ownership: owned-by-this-chain, foreign-dirty, generated/ignored,
  and deploy-sensitive.

Execution rules:
- Run slices serially unless the durable plan proves disjoint write sets,
  disjoint tests/state, and no shared deploy path.
- Do not rely on chat memory for resume state. Resume from the durable chain
  file, latest commit, log.md, and current git status.
- Do not revert or stage foreign-dirty files.
- Commit only this chain's staged changes, and include the active slug in the
  commit message.
- If runtime code or migrations changed, deploy only from the canonical
  deployment workspace after checks and after dirty-worktree rules are satisfied.

Per-slice completion checklist:
- Target files read directly after graph/index navigation.
- Implementation or documentation change is scoped to the slice.
- Relevant checks run, or exact blocker recorded.
- Source state committed with the slice slug, or exact commit blocker recorded.
- Runtime deploy/status checks run when required, or exact deploy blocker
  recorded.
- log.md or the chain reference records checks, commit, deploy state, blockers,
  changed files, and next slug.

Final handoff:
- Completed slugs.
- Commit hashes.
- Deploy status.
- Checks run and exact failures.
- Dirty/foreign files left untouched.
- Changed files.
- Next active slug or exhausted-chain statement.
```

Checklist for a coordinator before starting a worker:

- Confirm the slug queue and durable chain file.
- Confirm whether the chain is serial or parallel-safe.
- Record the initial dirty tracked and untracked files.
- Assign ownership for every expected write path.
- Name generated/vendor paths that are off limits.
- Name the exact checks and deploy decision rule.
- Require staged-only commits and explicit blocker logging.

## Slice 2: Agent Parallel Integrity Rules

Slug: `agent-parallel-integrity-rules`

Status: implemented.

Default to one serial worker for a chain. Parallel workers are allowed only when
all of these are true:

- The write sets are disjoint by file path and ownership boundary.
- The workers do not share a deployment path, deployment helper, migration path,
  release window, or runtime state.
- The workers do not share tests, fixtures, generated indexes, graph updates,
  temp files, caches, or external service state that could make results order
  dependent.
- Each worker can commit and hand off independently without staging or reverting
  another worker's files.
- One coordinator owns merge, graph/index refresh, deploy, and `log.md` updates
  after parallel work joins.

If any condition is uncertain, use a single serial worker. Documentation-only
chains that edit the same reference or `DEPLOYMENT.md` are not parallel-safe.

## Slice 3: Agent Unfinished Chain Recovery

Slug: `agent-unfinished-chain-recovery`

Status: implemented.

Recovery starts from durable state, not chat memory:

1. Read the chain file and identify the first slug not marked implemented,
   deployed, blocked, or superseded.
2. Read `git log --oneline -n 10` and the latest commit for the chain slug.
3. Read the current `log.md` entry for the chain date and any completed handoff
   file referenced by the chain.
4. Inspect `git status --short`, staged diff, unstaged diff, and untracked
   files. Attribute every dirty path to this chain, another user/worker, or
   generated output.
5. Re-run only the checks needed to validate the current slice boundary before
   continuing.
6. If state is ambiguous, record the ambiguity in the chain reference and stop
   before committing or deploying.

The recovery answer should name the slug being resumed, the commit hash or lack
of commit, current dirty-file ownership, checks already trusted, checks to
repeat, and the next command.

## Slice 4: Agent Worktree Branch Strategy

Slug: `agent-worktree-branch-strategy`

Status: implemented.

Decision:

- Use the main deployment workspace for short serial chains that can be checked,
  committed, and optionally deployed immediately.
- Use a branch per chain when work is long-running, review-heavy, or likely to
  pause before deployment.
- Use separate git worktrees for truly parallel chains so each worker has an
  isolated index and working tree.
- Merge back into the deployment workspace before deploy. The deploy handoff is
  owned by one coordinator from the canonical workspace.
- Do not deploy from a side worktree unless the operator explicitly confirms
  that the deploy wrapper and runtime path are configured for that worktree.

Branch/worktree names should include the chain slug. Before merging back,
re-read the chain file, latest commits, `log.md`, and current deploy workspace
status.

## Slice 5: Agent Dirty Worktree Guard

Slug: `agent-dirty-worktree-guard`

Status: implemented.

Preflight rule:

- Before checks, commits, deploy helpers, or broad sync/deploy wrappers, run
  `git status --short` and `git ls-files --others --exclude-standard`.
- Classify each dirty path as:
  - owned by the current chain;
  - foreign user/worker work;
  - generated or ignored output;
  - intentionally excluded from deploy;
  - unknown.
- Refuse broad commit, sync, deploy, migration, or status helpers when foreign
  or unknown dirty files could be staged, synced, deployed, or used by shared
  tests.
- Proceed only with staged-only commits for owned files, or after foreign files
  are excluded, stashed by their owner, committed by their owner, or explicitly
  confirmed safe by the operator.
- Record the dirty-file ownership and any excluded paths in the chain handoff.

The existing `scripts/chain-handoff.sh` behavior remains the conservative
default: it refuses unstaged tracked changes and untracked non-ignored files.
When unrelated local files are present, use manual staged-only commits and do
not run broad runtime deploy helpers until the deploy surface is clean or the
unrelated paths are explicitly excluded.

## Verification

Checks run:

- `bash scripts/reindex.sh` -> OK; rebuilt `CODE_INDEX.md`.
- `uv tool run --from graphifyy graphify update .` -> OK; rebuilt the code
  graph with 4685 nodes, 9295 edges, and 476 communities. The updater reported
  that document semantic updates require the AI `/graphify --update` flow.
- `git diff --check` -> OK.
- `bash -n scripts/chain-handoff.sh` -> OK.
- `bash -n deploy/bin/blagodarie-admin` -> OK.
- `bash -n deploy/install-blagodarie-admin-workflow.sh` -> OK.
- `python3 -m py_compile scripts/code_index.py` -> OK.

Runtime deploy is not required because this chain changes documentation and
process references only.

## Operational Handoff

- Implemented all five requested slugs in this durable chain reference.
- Updated `DEPLOYMENT.md` to link the reusable guardrails and summarize the
  operational defaults.
- Initial dirty worktree had foreign tracked changes in
  `telegram-bot/handler_rental.py`, `telegram-bot/settings.py`, and
  `telegram-bot/tests/test_handler_rental.py`, plus untracked
  `scripts/unblock-django-test-db.sh`.
- Those foreign paths were not edited or staged by this chain.
- Because unrelated local dirt remains, the broad `scripts/chain-handoff.sh`
  helper is intentionally not used for this commit. Use manual staged-only
  commit of this chain's owned files.

## Follow-Up Basket

No next implementation slug is selected by this process hardening chain.
