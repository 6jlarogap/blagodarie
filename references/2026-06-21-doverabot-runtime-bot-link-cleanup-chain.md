# Doverabot Runtime Bot Link Cleanup Chain

Date: 2026-06-21
Status: implemented and deployed
Started `/new-go-slug`: `doverabot-runtime-bot-link-cleanup`
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Prior hardening chain: [2026-06-21-doverabot-legacy-relatives-media-command-tests-chain.md](2026-06-21-doverabot-legacy-relatives-media-command-tests-chain.md)

## Scope

Continue legacy Doverabot hardening outside the rental path:

- replace remaining runtime hard-coded bot deep links where `bot_data.username` or shared helpers can provide the bot identity;
- keep settings, examples, docs, and backend links that already derive from settings out of scope;
- add a mocked bot regression around the changed sympathy contact handoff.

## Implemented

- Replaced the hard-coded `t.me/doverabot?start=...` sympathy contact handoff profile link with `Misc.get_deeplink(profile_from)`.
- Added a mocked `handler_sympas` test proving the contact handoff message uses the runtime `bot_data.username`.

## Verification

Passed before source commit:

- `python3 -m unittest telegram-bot/tests/test_handler_rental.py -k LegacySympaLinkTests`
- `python3 -m unittest discover telegram-bot/tests`
- `python3 -m py_compile telegram-bot/handler_sympas.py telegram-bot/tests/test_handler_rental.py`
- `python3 -m compileall telegram-bot`
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/`
- `uv tool run --from graphifyy graphify update .`

## Operational Handoff

Source commit:

- `git commit -m "doverabot-runtime-bot-link-cleanup"` -> `77ae6db`

Deploy checks:

- `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` -> OK; showed the expected bot source delta.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> OK with pre-existing `security.W002` clickjacking middleware warning.
- `sudo -n /usr/local/sbin/blagodarie-admin status` -> nginx, web, and bot active before deploy.
- `sudo -n /usr/local/sbin/blagodarie-admin sync` -> OK.
- `sudo -n /usr/local/sbin/blagodarie-admin migrate` -> no migrations to apply; same pre-existing `security.W002` warning.
- `sudo -n /usr/local/sbin/blagodarie-admin deploy` -> OK; nginx config test passed and web/bot restarted.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot active.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-web 60` -> recent Jun 21 web restart, no new traceback in the checked tail.
- `sudo -n /usr/local/sbin/blagodarie-admin logs-bot 80` -> recent Jun 21 bot restart, no new traceback in the checked tail.

## Follow-Up Basket

- Continue the separate profile-edit cleanup for remaining non-media direct callback splits in `handler_callbacks.py`.
- Keep replacing newly discovered hard-coded bot/deep links with runtime helpers as they are found.
