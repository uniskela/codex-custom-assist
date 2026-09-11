"""Tests for AI Task helpers and platform option defaults."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI_TASK_PATH = ROOT / "custom_components" / "codex_custom_assist" / "ai_task.py"
CONST_PATH = ROOT / "custom_components" / "codex_custom_assist" / "const.py"


def _load_const():
    name = "cca_const_under_test"
    if name in sys.modules:
        del sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, CONST_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_strip_helper():
    """Load strip_markdown_json_fence without importing Home Assistant platforms."""
    source = AI_TASK_PATH.read_text(encoding="utf-8")
    start = source.index("def strip_markdown_json_fence")
    end = source.index("\nasync def async_setup_entry")
    ns: dict = {}
    exec(source[start:end], ns)  # noqa: S102
    return ns["strip_markdown_json_fence"]


def test_strip_markdown_json_fence_plain() -> None:
    strip = _load_strip_helper()
    assert strip('{"ok": true}') == '{"ok": true}'


def test_strip_markdown_json_fence_fenced() -> None:
    strip = _load_strip_helper()
    raw = '```json\n{"room": "kitchen"}\n```'
    assert strip(raw) == '{"room": "kitchen"}'


def test_recommended_audio_defaults() -> None:
    const = _load_const()
    assert const.RECOMMENDED_STT_MODEL == "whisper-1"
    assert const.RECOMMENDED_TTS_MODEL == "tts-1"
    assert const.RECOMMENDED_TTS_VOICE == "alloy"
    assert const.RECOMMENDED_TTS_SPEED == 1.0
    assert "alloy" in const.TTS_VOICES
    assert "en-US" in const.SUPPORTED_AUDIO_LANGUAGES


def test_platform_option_keys_exist() -> None:
    const = _load_const()
    assert const.CONF_STT_MODEL == "stt_model"
    assert const.CONF_TTS_MODEL == "tts_model"
    assert const.CONF_AI_TASK_MODEL == "ai_task_model"


def test_structure_prompt_includes_schema_json() -> None:
    """AI Task must serialize structure into the system prompt (must-fix)."""
    source = AI_TASK_PATH.read_text(encoding="utf-8")
    assert "_schema_to_openai" in source
    assert "json_schema" in source
    assert "Respond with ONLY a valid JSON object matching this JSON Schema" in source


def test_tts_retries_instructions_on_openai_error() -> None:
    """TTS must soft-retry without instructions= on OpenAIError (must-fix)."""
    tts_path = ROOT / "custom_components" / "codex_custom_assist" / "tts.py"
    source = tts_path.read_text(encoding="utf-8")
    assert "except (TypeError, OpenAIError)" in source
    assert 'create_kwargs.pop("instructions", None)' in source
    assert "TTS retrying without instructions=" in source
