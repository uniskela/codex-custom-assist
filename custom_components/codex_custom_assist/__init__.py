"""The Codex Custom Assist integration — OpenAI-compatible Assist for Home Assistant."""

from __future__ import annotations

import openai
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .client import create_async_client, normalize_base_url
from .const import CONF_BASE_URL, DOMAIN, LOGGER

PLATFORMS = (
    Platform.AI_TASK,
    Platform.CONVERSATION,
    Platform.STT,
    Platform.TTS,
)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type CodexCustomAssistConfigEntry = ConfigEntry[openai.AsyncOpenAI]


async def async_setup_entry(
    hass: HomeAssistant, entry: CodexCustomAssistConfigEntry
) -> bool:
    """Set up Codex Custom Assist from a config entry."""
    try:
        base_url = normalize_base_url(entry.data[CONF_BASE_URL])
    except ValueError as err:
        raise ConfigEntryNotReady(str(err)) from err

    client = create_async_client(
        hass,
        api_key=entry.data.get(CONF_API_KEY, ""),
        base_url=base_url,
    )

    try:
        await client.models.list(timeout=15.0)
    except openai.AuthenticationError as err:
        raise ConfigEntryAuthFailed(err) from err
    except openai.NotFoundError:
        LOGGER.info(
            "Provider has no /models endpoint; proceeding with configured client"
        )
    except openai.APIStatusError as err:
        if err.status_code not in {404, 405, 501}:
            raise ConfigEntryNotReady(err) from err
        LOGGER.info(
            "Provider rejected /models (%s); proceeding with configured client",
            err.status_code,
        )
    except openai.OpenAIError as err:
        raise ConfigEntryNotReady(err) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    LOGGER.debug(
        "Codex Custom Assist ready (base_url=%s, llm_api=%s)",
        base_url,
        entry.options.get(CONF_LLM_HASS_API),
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: CodexCustomAssistConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant, entry: CodexCustomAssistConfigEntry
) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry versions if needed."""
    _ = hass
    if entry.version > 1:
        return False
    return True
