# Doverabot rental LLM extractor runtime rollout checklist

Date: 2026-06-25
Status: source-only runtime wiring prepared; live activation remains blocked on explicit human/admin approval.

## Scope

This reference documents the future live gate for the Doverabot rental LLM extractor.
It does **not** activate the service, write runtime settings, read secrets, call a provider, or restart the bot.

The source path prepared by the runtime-wiring child is:

- adapter source: `telegram-bot/rental_llm_extractor_adapter.py`
- requirements: `pip-rental-llm-extractor.txt`
- admin wrapper source: `deploy/bin/blagodarie-admin`
- bot settings surface: `telegram-bot/settings.py` and `telegram-bot/settings_local.py.example`

## Runtime surfaces

Bot-facing settings, managed through existing bot runtime settings after deployment:

- `RENTAL_LLM_EXTRACTOR_URL` — expected local value after service activation: `http://127.0.0.1:8767/extract`
- `RENTAL_LLM_EXTRACTOR_TOKEN` — optional shared token between bot and extractor endpoint
- `RENTAL_LLM_EXTRACTOR_CONTRACT` — `doverabot_rental_llm_extractor_v1`
- `RENTAL_LLM_EXTRACTOR_MODEL` — optional model label sent in request metadata
- `RENTAL_LLM_EXTRACTOR_TIMEOUT` — bot HTTP timeout for extractor requests

Extractor EnvironmentFile settings in `/etc/default/doverabot-rental-llm-extractor`, managed by `blagodarie-admin rental-llm-env`:

- `RENTAL_LLM_PROVIDER_URL`
- `RENTAL_LLM_PROVIDER_API_KEY` — secret; status output must be redacted
- `RENTAL_LLM_PROVIDER_MODEL`
- `RENTAL_LLM_PROVIDER_TIMEOUT`
- `RENTAL_LLM_PROVIDER_MAX_TIMEOUT`
- `RENTAL_LLM_PROVIDER_TEMPERATURE`
- `RENTAL_LLM_PROVIDER_MAX_TOKENS`
- `RENTAL_LLM_EXTRACTOR_PORT`
- `RENTAL_LLM_EXTRACTOR_MAX_TEXT_CHARS`
- `RENTAL_LLM_EXTRACTOR_LOG_TEXT_LIMIT`

## Future live gate checklist

Run only after explicit approval for wrapper install, service install/start/restart, runtime settings, provider secret configuration, bot restart, and synthetic smoke verification.

1. Install/update the wrapper from the source checkout:

   ```bash
   sudo bash deploy/install-blagodarie-admin-workflow.sh
   ```

2. Install the extractor venv and systemd unit from source:

   ```bash
   sudo -n /usr/local/sbin/blagodarie-admin install-rental-llm-extractor
   ```

3. Set extractor provider runtime env through redacted wrapper commands. Do not paste or log secret values in chat/wiki:

   ```bash
   sudo -n /usr/local/sbin/blagodarie-admin rental-llm-env set RENTAL_LLM_PROVIDER_URL <openai-compatible-chat-url>
   sudo -n /usr/local/sbin/blagodarie-admin rental-llm-env set RENTAL_LLM_PROVIDER_MODEL <model-name>
   sudo -n /usr/local/sbin/blagodarie-admin rental-llm-env set RENTAL_LLM_PROVIDER_API_KEY <secret-from-admin-shell>
   sudo -n /usr/local/sbin/blagodarie-admin rental-llm-env set RENTAL_LLM_EXTRACTOR_PORT 8767
   sudo -n /usr/local/sbin/blagodarie-admin rental-llm-env status all
   ```

4. Configure bot-facing runtime settings only after the extractor service exists:

   ```bash
   sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting set RENTAL_LLM_EXTRACTOR_URL http://127.0.0.1:8767/extract
   sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting set RENTAL_LLM_EXTRACTOR_CONTRACT doverabot_rental_llm_extractor_v1
   sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting set RENTAL_LLM_EXTRACTOR_TIMEOUT 30
   sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting status all
   ```

5. Restart only the affected services after settings are present:

   ```bash
   sudo -n /usr/local/sbin/blagodarie-admin restart-rental-llm-extractor
   sudo -n /usr/local/sbin/blagodarie-admin status-rental-llm-extractor
   sudo -n /usr/local/sbin/blagodarie-admin restart-bot
   sudo -n /usr/local/sbin/blagodarie-admin is-active
   ```

6. Smoke with synthetic text only. Do not use production transcript dumps:

   ```bash
   curl -sS -X POST http://127.0.0.1:8767/extract \
     -H 'Content-Type: application/json' \
     -d @/tmp/doverabot-rental-llm-extractor-smoke.json
   ```

   Suggested synthetic payload uses `моноколесо`, `парадром Флай Чегем`, `1000 рублей`, and `на выходные`.

7. Inspect redacted logs only:

   ```bash
   sudo -n /usr/local/sbin/blagodarie-admin logs-rental-llm-extractor 120
   sudo -n /usr/local/sbin/blagodarie-admin logs-bot 120
   ```

## Rollback

- Clear bot-facing extractor URL to force deterministic fallback:

  ```bash
  sudo -n /usr/local/sbin/blagodarie-admin bot-runtime-setting clear RENTAL_LLM_EXTRACTOR_URL
  sudo -n /usr/local/sbin/blagodarie-admin restart-bot
  ```

- Stop/disable the extractor service only with explicit admin approval:

  ```bash
  sudo systemctl disable --now doverabot-rental-llm-extractor.service
  ```

Regex/deterministic extraction remains the fallback when `RENTAL_LLM_EXTRACTOR_URL` is empty, missing, slow, or malformed.
