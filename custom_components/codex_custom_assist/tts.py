"""Text-to-speech support for Codex Custom Assist."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, Literal, override

from openai import OpenAIError
from propcache.api import cached_property

from homeassistant.components.tts import (
    ATTR_PREFERRED_FORMAT,
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CodexCustomAssistConfigEntry
from .const import (
    CONF_TTS_MODEL,
    CONF_TTS_PROMPT,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_TTS_PROMPT,
    RECOMMENDED_TTS_MODEL,
    RECOMMENDED_TTS_SPEED,
    RECOMMENDED_TTS_VOICE,
    SUPPORTED_AUDIO_LANGUAGES,
    TTS_VOICES,
)
from .entity import CodexCustomAssistEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexCustomAssistConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TTS entity."""
    async_add_entities([CodexCustomAssistTTSEntity(config_entry)])


class CodexCustomAssistTTSEntity(TextToSpeechEntity, CodexCustomAssistEntity):
    """OpenAI-compatible text-to-speech entity."""

    _attr_supported_options = [ATTR_VOICE, ATTR_PREFERRED_FORMAT]
    _attr_supported_languages = list(SUPPORTED_AUDIO_LANGUAGES)
    _attr_default_language = "en-US"

    _supported_voices = [Voice(voice, voice.capitalize()) for voice in TTS_VOICES]
    _supported_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]

    def __init__(self, entry: CodexCustomAssistConfigEntry) -> None:
        """Initialize TTS entity."""
        # Short name with has_entity_name=True → "{title} TTS".
        super().__init__(entry, unique_id=f"{entry.entry_id}_tts", name="TTS")

    @callback
    @override
    def async_get_supported_voices(self, language: str) -> list[Voice]:
        """Return supported voices."""
        return self._supported_voices

    @cached_property
    @override
    def default_options(self) -> Mapping[str, Any]:
        """Return default TTS options."""
        return {
            ATTR_VOICE: self._option(CONF_TTS_VOICE, RECOMMENDED_TTS_VOICE),
            ATTR_PREFERRED_FORMAT: "mp3",
        }

    @override
    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Synthesize speech via /v1/audio/speech."""
        merged = {**dict(self.entry.options), **options}
        client = self.entry.runtime_data
        model = merged.get(CONF_TTS_MODEL, RECOMMENDED_TTS_MODEL)
        voice = merged.get(ATTR_VOICE, RECOMMENDED_TTS_VOICE)
        speed = float(merged.get(CONF_TTS_SPEED, RECOMMENDED_TTS_SPEED))
        instructions = str(merged.get(CONF_TTS_PROMPT, DEFAULT_TTS_PROMPT) or "")

        response_format = merged.get(
            ATTR_PREFERRED_FORMAT, self.default_options[ATTR_PREFERRED_FORMAT]
        )
        if response_format in ("ogg", "oga"):
            codec: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "opus"
        elif response_format == "raw":
            response_format = codec = "pcm"
        elif response_format not in self._supported_formats:
            response_format = self.default_options[ATTR_PREFERRED_FORMAT]
            codec = response_format
        else:
            codec = response_format

        create_kwargs: dict[str, Any] = {
            "model": model,
            "voice": voice,
            "input": message,
            "speed": speed,
            "response_format": codec,
        }
        if instructions:
            create_kwargs["instructions"] = instructions

        try:
            response_data = await self._stream_speech(client, create_kwargs)
        except (TypeError, OpenAIError) as err:
            # Classic models (tts-1) and many compat proxies reject instructions=.
            # SDK TypeError covers older clients; OpenAIError covers HTTP API rejects.
            if "instructions" not in create_kwargs:
                _LOGGER.exception(
                    "TTS failed (model=%s). Backend may not implement /v1/audio/speech",
                    model,
                )
                raise HomeAssistantError(
                    f"TTS not available on this OpenAI-compatible backend: {err}"
                ) from err
            create_kwargs.pop("instructions", None)
            _LOGGER.debug(
                "TTS retrying without instructions= (model=%s): %s", model, err
            )
            try:
                response_data = await self._stream_speech(client, create_kwargs)
            except OpenAIError as retry_err:
                _LOGGER.exception(
                    "TTS failed (model=%s). Backend may not implement /v1/audio/speech",
                    model,
                )
                raise HomeAssistantError(
                    f"TTS not available on this OpenAI-compatible backend: {retry_err}"
                ) from retry_err

        return response_format, bytes(response_data)

    async def _stream_speech(
        self, client: Any, create_kwargs: dict[str, Any]
    ) -> bytearray:
        """Stream /v1/audio/speech into a bytearray."""
        async with client.audio.speech.with_streaming_response.create(
            **create_kwargs
        ) as response:
            response_data = bytearray()
            async for chunk in response.iter_bytes():
                response_data.extend(chunk)
        return response_data
