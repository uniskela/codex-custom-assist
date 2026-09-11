"""Config flow for Codex Custom Assist."""

from __future__ import annotations

from typing import Any

import openai
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LLM_HASS_API,
    CONF_PROMPT,
)
from homeassistant.core import callback
from homeassistant.helpers import llm
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .client import async_validate_provider, normalize_base_url
from .const import (
    API_PROTOCOL_CHAT_COMPLETIONS,
    API_PROTOCOL_RESPONSES,
    CONF_API_PROTOCOL,
    CONF_BASE_URL,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_NAME,
    DOMAIN,
    LOGGER,
    RECOMMENDED_API_PROTOCOL,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        vol.Optional(CONF_API_KEY, default=DEFAULT_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_CHAT_MODEL, default=RECOMMENDED_CHAT_MODEL): str,
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        vol.Optional(CONF_API_KEY, default=DEFAULT_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
    }
)


def _options_schema(hass: Any, options: dict[str, Any]) -> vol.Schema:
    """Build options schema parallel to openai_conversation where applicable."""
    hass_apis = [
        SelectOptionDict(label=api.name, value=api.id)
        for api in llm.async_get_apis(hass)
    ]
    return vol.Schema(
        {
            vol.Optional(
                CONF_PROMPT,
                description={
                    "suggested_value": options.get(
                        CONF_PROMPT, llm.DEFAULT_INSTRUCTIONS_PROMPT
                    )
                },
            ): TemplateSelector(),
            vol.Optional(
                CONF_LLM_HASS_API,
                description={"suggested_value": options.get(CONF_LLM_HASS_API)},
            ): SelectSelector(
                SelectSelectorConfig(
                    options=hass_apis,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_CHAT_MODEL,
                default=options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
            ): str,
            vol.Required(
                CONF_API_PROTOCOL,
                default=options.get(CONF_API_PROTOCOL, RECOMMENDED_API_PROTOCOL),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(
                            label="Chat Completions (/v1/chat/completions)",
                            value=API_PROTOCOL_CHAT_COMPLETIONS,
                        ),
                        SelectOptionDict(
                            label="Responses (/v1/responses)",
                            value=API_PROTOCOL_RESPONSES,
                        ),
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key=CONF_API_PROTOCOL,
                )
            ),
            vol.Required(
                CONF_MAX_TOKENS,
                default=options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1, max=128000, step=1, mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_TEMPERATURE,
                default=options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=2, step=0.05, mode=NumberSelectorMode.SLIDER
                )
            ),
            vol.Required(
                CONF_TOP_P,
                default=options.get(CONF_TOP_P, RECOMMENDED_TOP_P),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=1, step=0.05, mode=NumberSelectorMode.SLIDER
                )
            ),
        }
    )


async def _validate_connection(
    hass: Any, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate and normalize connection fields."""
    normalized_url = normalize_base_url(data[CONF_BASE_URL])
    api_key = data.get(CONF_API_KEY) or DEFAULT_API_KEY
    await async_validate_provider(
        hass,
        api_key=api_key,
        base_url=normalized_url,
    )
    return {
        CONF_BASE_URL: normalized_url,
        CONF_API_KEY: api_key,
    }


class CodexCustomAssistConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Codex Custom Assist."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return CodexCustomAssistOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            model = user_input.get(CONF_CHAT_MODEL, "").strip()
            if not model:
                errors[CONF_CHAT_MODEL] = "invalid_model"
            else:
                try:
                    connection = await _validate_connection(self.hass, user_input)
                except ValueError:
                    errors[CONF_BASE_URL] = "invalid_url"
                except openai.AuthenticationError:
                    errors["base"] = "invalid_auth"
                except openai.APIConnectionError:
                    errors["base"] = "cannot_connect"
                except openai.OpenAIError:
                    LOGGER.exception(
                        "API error while validating Codex Custom Assist provider"
                    )
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001
                    LOGGER.exception(
                        "Unexpected error validating Codex Custom Assist provider"
                    )
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(connection[CONF_BASE_URL].lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"{DEFAULT_NAME} ({model})",
                        data=connection,
                        options={
                            CONF_CHAT_MODEL: model,
                            CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
                            CONF_API_PROTOCOL: RECOMMENDED_API_PROTOCOL,
                            CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
                            CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
                            CONF_TOP_P: RECOMMENDED_TOP_P,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
            description_placeholders={
                "codex_lb_url": DEFAULT_BASE_URL,
                "example_generic": "http://litellm:4000/v1",
            },
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth when API authentication fails."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication with a new API key / base URL."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        current = {
            CONF_BASE_URL: entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
            CONF_API_KEY: entry.data.get(CONF_API_KEY, DEFAULT_API_KEY),
        }

        if user_input is not None:
            try:
                connection = await _validate_connection(self.hass, user_input)
            except ValueError:
                errors[CONF_BASE_URL] = "invalid_url"
            except openai.AuthenticationError:
                errors["base"] = "invalid_auth"
            except openai.APIConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected reauth error")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=connection,
                    unique_id=connection[CONF_BASE_URL].lower(),
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                STEP_REAUTH_DATA_SCHEMA, user_input or current
            ),
            errors=errors,
        )


class CodexCustomAssistOptionsFlow(OptionsFlow):
    """Handle Codex Custom Assist options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        options = dict(self.config_entry.options)

        if user_input is not None:
            if not user_input.get(CONF_CHAT_MODEL, "").strip():
                errors[CONF_CHAT_MODEL] = "invalid_model"
            else:
                if not user_input.get(CONF_LLM_HASS_API):
                    user_input.pop(CONF_LLM_HASS_API, None)
                user_input[CONF_CHAT_MODEL] = user_input[CONF_CHAT_MODEL].strip()
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                _options_schema(self.hass, options), options
            ),
            errors=errors,
        )
