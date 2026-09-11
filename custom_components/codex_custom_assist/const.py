"""Constants for the Codex Custom Assist integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "codex_custom_assist"
LOGGER = logging.getLogger(__package__)

CONF_BASE_URL: Final = "base_url"
CONF_CHAT_MODEL: Final = "chat_model"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_TEMPERATURE: Final = "temperature"
CONF_TOP_P: Final = "top_p"
CONF_API_PROTOCOL: Final = "api_protocol"
CONF_RECOMMENDED: Final = "recommended"

API_PROTOCOL_CHAT_COMPLETIONS: Final = "chat_completions"
API_PROTOCOL_RESPONSES: Final = "responses"

DEFAULT_NAME: Final = "Codex Custom Assist"
DEFAULT_CONVERSATION_NAME: Final = "Codex Custom Assist Conversation"

# Codex-LB OpenAI-compatible default (override for other backends).
DEFAULT_BASE_URL: Final = "http://127.0.0.1:2455/v1"
DEFAULT_API_KEY: Final = "sk-placeholder"

RECOMMENDED_CHAT_MODEL: Final = "gpt-5.3-codex"
RECOMMENDED_MAX_TOKENS: Final = 2048
RECOMMENDED_TEMPERATURE: Final = 0.7
RECOMMENDED_TOP_P: Final = 1.0
RECOMMENDED_API_PROTOCOL: Final = API_PROTOCOL_CHAT_COMPLETIONS

MAX_TOOL_ITERATIONS: Final = 10
