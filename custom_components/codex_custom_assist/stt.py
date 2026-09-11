"""Speech-to-text support for Codex Custom Assist."""

from __future__ import annotations

from collections.abc import AsyncIterable
import io
import logging
import wave
from typing import override

from openai import OpenAIError

from homeassistant.components import stt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CodexCustomAssistConfigEntry
from .const import (
    CONF_STT_MODEL,
    CONF_STT_PROMPT,
    DEFAULT_STT_PROMPT,
    RECOMMENDED_STT_MODEL,
    SUPPORTED_AUDIO_LANGUAGES,
)
from .entity import CodexCustomAssistEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexCustomAssistConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STT entity."""
    async_add_entities([CodexCustomAssistSTTEntity(config_entry)])


class CodexCustomAssistSTTEntity(stt.SpeechToTextEntity, CodexCustomAssistEntity):
    """OpenAI-compatible speech-to-text entity."""

    def __init__(self, entry: CodexCustomAssistConfigEntry) -> None:
        """Initialize STT entity."""
        # Short name with has_entity_name=True → "{title} STT".
        super().__init__(entry, unique_id=f"{entry.entry_id}_stt", name="STT")

    @property
    @override
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return list(SUPPORTED_AUDIO_LANGUAGES)

    @property
    @override
    def supported_formats(self) -> list[stt.AudioFormats]:
        """Return supported formats."""
        return [stt.AudioFormats.WAV, stt.AudioFormats.OGG]

    @property
    @override
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        """Return supported codecs."""
        return [stt.AudioCodecs.PCM, stt.AudioCodecs.OPUS]

    @property
    @override
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        """Return supported bit rates."""
        return [
            stt.AudioBitRates.BITRATE_8,
            stt.AudioBitRates.BITRATE_16,
            stt.AudioBitRates.BITRATE_24,
            stt.AudioBitRates.BITRATE_32,
        ]

    @property
    @override
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        """Return supported sample rates."""
        return [
            stt.AudioSampleRates.SAMPLERATE_8000,
            stt.AudioSampleRates.SAMPLERATE_16000,
            stt.AudioSampleRates.SAMPLERATE_22000,
            stt.AudioSampleRates.SAMPLERATE_44100,
            stt.AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    @override
    def supported_channels(self) -> list[stt.AudioChannels]:
        """Return supported channels."""
        return [stt.AudioChannels.CHANNEL_MONO, stt.AudioChannels.CHANNEL_STEREO]

    @override
    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Transcribe an audio stream via /v1/audio/transcriptions."""
        audio_bytes = bytearray()
        async for chunk in stream:
            audio_bytes.extend(chunk)
        audio_data = bytes(audio_bytes)

        if metadata.format == stt.AudioFormats.WAV:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(metadata.channel.value)
                wf.setsampwidth(metadata.bit_rate.value // 8)
                wf.setframerate(metadata.sample_rate.value)
                wf.writeframes(audio_data)
            audio_data = wav_buffer.getvalue()

        model = self._option(CONF_STT_MODEL, RECOMMENDED_STT_MODEL)
        prompt = self._option(CONF_STT_PROMPT, DEFAULT_STT_PROMPT)
        client = self.entry.runtime_data

        try:
            response = await client.audio.transcriptions.create(
                model=model,
                file=(f"a.{metadata.format.value}", audio_data),
                response_format="json",
                language=metadata.language.split("-")[0],
                prompt=prompt,
            )
        except OpenAIError:
            _LOGGER.exception(
                "STT failed (model=%s). Backend may not implement "
                "/v1/audio/transcriptions",
                model,
            )
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

        if response.text:
            return stt.SpeechResult(response.text, stt.SpeechResultState.SUCCESS)
        return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
