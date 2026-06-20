#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/chain-handoff.sh --new-go-slug SLUG [--runtime] [--logs] [--no-commit]

Runs the standard chain-success handoff from the editable workspace.

Steps:
  1. Run source checks for handoff scripts and staged changes.
  2. Commit already-staged changes with the /new go slug, unless --no-commit is set.
  3. With --runtime, run the deployment wrapper sequence:
     deploy-dry-run, sync, migrate, deploy, is-active.
  4. With --logs, show recent web and bot logs after the active check.

The script commits only staged changes. It refuses unstaged tracked changes and
untracked non-ignored files so unrelated local work is not swept into a chain
commit by accident.
USAGE
}

slug=""
run_runtime=0
show_logs=0
do_commit=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --new-go-slug)
      shift
      if [[ $# -eq 0 || "${1:0:1}" == "-" ]]; then
        echo "Missing value for --new-go-slug." >&2
        usage >&2
        exit 2
      fi
      if [[ -n "$slug" ]]; then
        echo "Duplicate --new-go-slug." >&2
        usage >&2
        exit 2
      fi
      slug="$1"
      ;;
    --runtime)
      run_runtime=1
      ;;
    --logs)
      show_logs=1
      ;;
    --no-commit)
      do_commit=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      echo "Unexpected positional argument: $1" >&2
      echo "Use --new-go-slug SLUG so the chain handoff records the /new go slug explicitly." >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ -z "$slug" ]]; then
  echo "Missing mandatory --new-go-slug SLUG." >&2
  usage >&2
  exit 2
fi

if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "Invalid /new go slug: $slug" >&2
  echo "Use lowercase letters, digits, and hyphens; start with a letter or digit." >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

admin=(sudo -n /usr/local/sbin/blagodarie-admin)

run() {
  printf '\n+'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}

require_clean_unstaged_state() {
  local untracked

  if ! git diff --quiet; then
    echo "Refusing handoff with unstaged tracked changes:" >&2
    git status --short >&2
    exit 1
  fi

  untracked="$(git ls-files --others --exclude-standard)"
  if [[ -n "$untracked" ]]; then
    echo "Refusing handoff with untracked non-ignored files:" >&2
    printf '%s\n' "$untracked" >&2
    exit 1
  fi
}

require_no_staged_changes() {
  if ! git diff --cached --quiet; then
    echo "Refusing runtime deploy with staged uncommitted changes:" >&2
    git status --short >&2
    exit 1
  fi
}

run_source_checks() {
  run git diff --check
  run git diff --cached --check
  run bash -n scripts/chain-handoff.sh
  run bash -n deploy/bin/blagodarie-admin
  run bash -n deploy/install-blagodarie-admin-workflow.sh
  run bash -n scripts/reindex.sh
  run python3 -m py_compile scripts/code_index.py
}

commit_staged_changes() {
  if [[ "$do_commit" != "1" ]]; then
    echo "Commit step skipped by --no-commit."
    return
  fi

  require_clean_unstaged_state

  if git diff --cached --quiet; then
    echo "No staged changes to commit; keeping current HEAD."
    return
  fi

  run git commit -m "$slug"
}

run_runtime_handoff() {
  if [[ "$run_runtime" != "1" ]]; then
    echo "Runtime deploy skipped; pass --runtime when migrations or runtime code changed."
    return
  fi

  require_clean_unstaged_state
  require_no_staged_changes

  run "${admin[@]}" deploy-dry-run
  run "${admin[@]}" sync
  run "${admin[@]}" migrate
  run "${admin[@]}" deploy
  run "${admin[@]}" is-active

  if [[ "$show_logs" == "1" ]]; then
    run "${admin[@]}" logs-web 80
    run "${admin[@]}" logs-bot 80
  fi
}

run_source_checks
commit_staged_changes
run_runtime_handoff

echo
echo "Chain handoff completed for: $slug"
