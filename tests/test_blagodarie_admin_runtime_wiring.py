from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADMIN = (ROOT / "deploy" / "bin" / "blagodarie-admin").read_text(encoding="utf-8")
SETTINGS = (ROOT / "telegram-bot" / "settings.py").read_text(encoding="utf-8")
LOCAL_SETTINGS_EXAMPLE = (ROOT / "telegram-bot" / "settings_local.py.example").read_text(encoding="utf-8")
HANDLER_RENTAL = (ROOT / "telegram-bot" / "handler_rental.py").read_text(encoding="utf-8")
REQUIREMENTS = (ROOT / "pip-rental-llm-extractor.txt").read_text(encoding="utf-8")


def test_admin_wrapper_exposes_source_only_llm_extractor_commands_and_service_paths():
    assert "RENTAL_LLM_EXTRACTOR_SERVICE=doverabot-rental-llm-extractor.service" in ADMIN
    assert "RENTAL_LLM_EXTRACTOR_VENV=\"$DST/venv-rental-llm-extractor\"" in ADMIN
    assert "RENTAL_LLM_EXTRACTOR_ADAPTER=\"$DST/telegram-bot/rental_llm_extractor_adapter.py\"" in ADMIN
    assert "RENTAL_LLM_EXTRACTOR_ENV_FILE=/etc/default/doverabot-rental-llm-extractor" in ADMIN
    assert "--exclude '/venv-rental-llm-extractor/'" in ADMIN

    for command in (
        "install-rental-llm-extractor",
        "deploy-rental-llm-extractor",
        "restart-rental-llm-extractor",
        "status-rental-llm-extractor",
        "is-active-rental-llm-extractor",
        "logs-rental-llm-extractor",
        "rental-llm-env",
    ):
        assert command in ADMIN


def test_admin_wrapper_allowlists_and_redacts_llm_provider_env_settings():
    for key in (
        "RENTAL_LLM_PROVIDER_URL",
        "RENTAL_LLM_PROVIDER_API_KEY",
        "RENTAL_LLM_PROVIDER_MODEL",
        "RENTAL_LLM_PROVIDER_TIMEOUT",
        "RENTAL_LLM_PROVIDER_MAX_TIMEOUT",
        "RENTAL_LLM_PROVIDER_TEMPERATURE",
        "RENTAL_LLM_PROVIDER_MAX_TOKENS",
        "RENTAL_LLM_EXTRACTOR_PORT",
        "RENTAL_LLM_EXTRACTOR_MAX_TEXT_CHARS",
        "RENTAL_LLM_EXTRACTOR_LOG_TEXT_LIMIT",
    ):
        assert key in ADMIN

    assert "Secret values such as RENTAL_LLM_PROVIDER_API_KEY are reported only as redacted" in ADMIN
    assert "suffix = \" (redacted)\"" in ADMIN
    assert "Values are written to the extractor EnvironmentFile and are never printed." in ADMIN
    assert "rendered_value = shlex.quote(value)" in ADMIN


def test_python_settings_document_bot_vs_adapter_runtime_boundaries():
    assert "RENTAL_LLM_EXTRACTOR_CONTRACT = 'doverabot_rental_llm_extractor_v1'" in SETTINGS
    assert "RENTAL_LLM_EXTRACTOR_URL = ''" in SETTINGS
    assert "RENTAL_LLM_EXTRACTOR_TIMEOUT = 30" in SETTINGS
    assert "Adapter provider/runtime env is intentionally not imported by the bot" in SETTINGS
    assert "Do not put real provider tokens into logs, docs, or this source tree." in SETTINGS

    assert "RENTAL_LLM_EXTRACTOR_URL = 'http://127.0.0.1:8767/extract'" in LOCAL_SETTINGS_EXAMPLE
    assert "managed by `blagodarie-admin rental-llm-env`, not Python settings" in LOCAL_SETTINGS_EXAMPLE


def test_llm_runtime_requirements_and_bot_debug_redaction_are_present():
    assert REQUIREMENTS.strip().splitlines() == ["aiohttp"]
    assert "SECRET_LOG_KEY_MARKERS = {'authorization', 'api_key', 'token', 'secret', 'password'}" in HANDLER_RENTAL
    assert "return '[redacted]'" in HANDLER_RENTAL
