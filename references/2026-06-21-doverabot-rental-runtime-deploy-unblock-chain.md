# Doverabot Rental Runtime Deploy Unblock Chain

Date: 2026-06-21
Status: implemented and deployed
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

The user installed the updated wrapper from an authenticated shell:

```bash
sudo bash deploy/install-blagodarie-admin-workflow.sh
```

After that, the deploy-unblock sequence completed.

## Permission Helper

- Added `scripts/enable-agent-deploy-permissions.sh` as a repeatable root-run
  bootstrap that installs the narrow wrapper and verifies noninteractive
  `deploy-dry-run` access for `vdrzd`.
- Documented the helper in `DEPLOYMENT.md`.
- `git commit -m "add agent deploy permission bootstrap"` -> `2040692`.

## Runtime Handoff

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` captured to
  `/tmp/blagodarie-deploy-dry-run.txt` -> OK; the dry-run no longer includes
  `scripts/unblock-django-test-db.sh`.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> applied
  `users.0061_rental_payment_proof_rejected_event` and
  `users.0062_rentaloffer_quantity_total`; existing `security.W002`
  clickjacking middleware warning remains.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; Django check passed
  with the same existing warning and nginx config test was successful.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot
  all active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 100` and `logs-bot 100`
  -> expected restart history after the 2026-06-21 19:42 MSK deploy with no
  traceback in the captured output.

## Public Smokes

- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'`
  -> HTTP 200, `{"offers":[]}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/user/points/?rental=on&rental_query=tent&rental_price_max=600&number=1'`
  -> HTTP 200, empty `points`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/offer/'`
  -> expected HTTP 404, `{}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/reservation/?tg_token=bad&user_uuid=00000000-0000-0000-0000-000000000000'`
  -> expected HTTP 400, `{"message":"Неверный токен телеграм бота"}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://map.doverabot.ru/?rental=on'`
  -> HTTP 200 and returned the rental map wrapper.

The unrelated untracked `scripts/unblock-django-test-db.sh` helper remains
untracked and was not deployed.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-next-decision-refresh`
