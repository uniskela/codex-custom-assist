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

CONF_STT_MODEL: Final = "stt_model"
CONF_STT_PROMPT: Final = "stt_prompt"
CONF_TTS_MODEL: Final = "tts_model"
CONF_TTS_VOICE: Final = "tts_voice"
CONF_TTS_SPEED: Final = "tts_speed"
CONF_TTS_PROMPT: Final = "tts_prompt"
CONF_AI_TASK_MODEL: Final = "ai_task_model"

API_PROTOCOL_CHAT_COMPLETIONS: Final = "chat_completions"
API_PROTOCOL_RESPONSES: Final = "responses"

DEFAULT_NAME: Final = "Codex Custom Assist"
DEFAULT_CONVERSATION_NAME: Final = "Codex Custom Assist Conversation"
DEFAULT_STT_NAME: Final = "Codex Custom Assist STT"
DEFAULT_TTS_NAME: Final = "Codex Custom Assist TTS"
DEFAULT_AI_TASK_NAME: Final = "Codex Custom Assist AI Task"

# Codex-LB OpenAI-compatible default (override for other backends).
DEFAULT_BASE_URL: Final = "http://127.0.0.1:2455/v1"
DEFAULT_API_KEY: Final = "sk-placeholder"

RECOMMENDED_CHAT_MODEL: Final = "gpt-5.3-codex"
RECOMMENDED_MAX_TOKENS: Final = 2048
RECOMMENDED_TEMPERATURE: Final = 0.7
RECOMMENDED_TOP_P: Final = 1.0
RECOMMENDED_API_PROTOCOL: Final = API_PROTOCOL_CHAT_COMPLETIONS

# Prefer broadly supported OpenAI-compatible audio model ids.
RECOMMENDED_STT_MODEL: Final = "whisper-1"
RECOMMENDED_TTS_MODEL: Final = "tts-1"
RECOMMENDED_TTS_VOICE: Final = "alloy"
RECOMMENDED_TTS_SPEED: Final = 1.0
DEFAULT_STT_PROMPT: Final = (
    "The following conversation is a smart home user talking to Home Assistant."
)
DEFAULT_TTS_PROMPT: Final = ""

MAX_TOOL_ITERATIONS: Final = 10

# Shared language list used by STT/TTS (OpenAI speech docs).
SUPPORTED_AUDIO_LANGUAGES: Final = [
    "af-ZA",
    "ar-SA",
    "hy-AM",
    "az-AZ",
    "be-BY",
    "bs-BA",
    "bg-BG",
    "ca-ES",
    "zh-CN",
    "hr-HR",
    "cs-CZ",
    "da-DK",
    "nl-NL",
    "en-US",
    "et-EE",
    "fi-FI",
    "fr-FR",
    "gl-ES",
    "de-DE",
    "el-GR",
    "he-IL",
    "hi-IN",
    "hu-HU",
    "is-IS",
    "id-ID",
    "it-IT",
    "ja-JP",
    "kn-IN",
    "kk-KZ",
    "ko-KR",
    "lv-LV",
    "lt-LT",
    "mk-MK",
    "ms-MY",
    "mr-IN",
    "mi-NZ",
    "ne-NP",
    "no-NO",
    "fa-IR",
    "pl-PL",
    "pt-PT",
    "ro-RO",
    "ru-RU",
    "sr-RS",
    "sk-SK",
    "sl-SI",
    "es-ES",
    "sw-KE",
    "sv-SE",
    "fil-PH",
    "ta-IN",
    "th-TH",
    "tr-TR",
    "uk-UA",
    "ur-PK",
    "vi-VN",
    "cy-GB",
]

TTS_VOICES: Final = (
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "fable",
    "nova",
    "onyx",
    "sage",
    "shimmer",
    "verse",
    "marin",
    "cedar",
)
