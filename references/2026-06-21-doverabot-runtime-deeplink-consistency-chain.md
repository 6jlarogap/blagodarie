# Doverabot Runtime Deeplink Consistency Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-runtime-deeplink-consistency`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)

## Scope

Finish a small runtime deeplink consistency slice across newly touched bot
flows:

- audit bot runtime links for hard-coded bot usernames and duplicated Telegram
  start-link construction;
- keep settings, examples, docs, backend links, and configured host constants
  out of scope;
- route representative meet, offer, rental, and profile start links through a
  shared runtime helper;
- add mocked regressions proving runtime bot usernames and existing payloads
  stay compatible.

## Implemented

- Added `Misc.get_start_deeplink(start_payload, https=False)` as the single
  helper for bot start links.
- Routed profile deeplinks, meet card links, meet QR links, offer links, and
  rental links through the shared helper.
- Preserved existing payload formats:
  - `meet`
  - `m-<meet_id>`
  - `offer-<offer_uuid>` plus optional `-userId-<ref>`
  - `rent-<offer_uuid>`
  - profile username/UUID payloads.
- Added mocked regression coverage for `common`, `handler_callbacks`,
  `handler_offer`, `handler_rental`, and the prior sympathy handoff runtime
  username path.

## Verification

Passed before source commit:

- `rg -n "t\.me/\{bot_data\.username\}\?start=|https://t\.me/\{bot_data\.username\}\?start=|doverabot\?start|t\.me/doverabot" telegram-bot --glob '!settings.py' --glob '!settings_local.py.example'` -> only the centralized helper remains.
- `python3 -m unittest telegram-bot/tests/test_handler_rental.py -k Deeplink` -> 3 tests OK.
- `python3 -m unittest discover telegram-bot/tests` -> 68 tests OK.
- `python3 -m py_compile telegram-bot/common.py telegram-bot/handler_callbacks.py telegram-bot/handler_offer.py telegram-bot/handler_rental.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> no issues.
- `uv tool run --from graphifyy graphify update .` -> rebuilt code graph
  with 4366 nodes, 8706 edges, and 438 communities.

## Operational Handoff

Source commit:

- `git commit -m "doverabot-runtime-deeplink-consistency"` -> `44729d7`

Deploy checks:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with
  pre-existing `security.W002` clickjacking middleware warning.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx, web, and bot
  active before deploy.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply;
  same pre-existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test
  passed and web/bot restarted.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot
  active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 80` -> recent Jun 21 web
  restart, no traceback in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 100` -> recent Jun 21 bot
  restart, no traceback in the checked tail.

## Follow-Up Basket

- Continue the ordered go-next chain in
  [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md).
- Suggested next `/new-go-slug`: `doverabot-handler-test-harness-split`.
- The next slice plan already prints its own successor: after
  `doverabot-handler-test-harness-split`, print
  `doverabot-rental-v1-smoke-observability`.
