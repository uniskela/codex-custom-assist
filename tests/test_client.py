"""Tests for Codex Custom Assist provider helpers (no Home Assistant runtime)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "custom_components" / "codex_custom_assist" / "client.py"


def _load_client_module():
    """Load client.py without importing the Home Assistant package graph."""
    # Provide lightweight stubs for HA imports used at module import time.
    import types

    if "homeassistant" not in sys.modules:
        ha = types.ModuleType("homeassistant")
        ha_core = types.ModuleType("homeassistant.core")
        ha_helpers = types.ModuleType("homeassistant.helpers")
        ha_httpx = types.ModuleType("homeassistant.helpers.httpx_client")

        class _HomeAssistant:
            pass

        def _get_async_client(_hass):
            return None

        ha_core.HomeAssistant = _HomeAssistant
        ha_httpx.get_async_client = _get_async_client
        sys.modules["homeassistant"] = ha
        sys.modules["homeassistant.core"] = ha_core
        sys.modules["homeassistant.helpers"] = ha_helpers
        sys.modules["homeassistant.helpers.httpx_client"] = ha_httpx

    if "openai" not in sys.modules:
        sys.modules["openai"] = types.ModuleType("openai")
        sys.modules["openai"].AsyncOpenAI = object

    # Stub relative const import used by client.py
    const_name = "custom_components.codex_custom_assist.const"
    if const_name not in sys.modules:
        const_mod = types.ModuleType(const_name)
        const_mod.API_PROTOCOL_CHAT_COMPLETIONS = "chat_completions"
        const_mod.API_PROTOCOL_RESPONSES = "responses"
        import logging

        const_mod.LOGGER = logging.getLogger("codex_custom_assist.test")
        pkg = types.ModuleType("custom_components")
        pkg_assist = types.ModuleType("custom_components.codex_custom_assist")
        sys.modules["custom_components"] = pkg
        sys.modules["custom_components.codex_custom_assist"] = pkg_assist
        sys.modules[const_name] = const_mod

    mod_name = "custom_components.codex_custom_assist.client"
    spec = importlib.util.spec_from_file_location(mod_name, CLIENT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "custom_components.codex_custom_assist"
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


client = _load_client_module()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://127.0.0.1:2455/v1", "http://127.0.0.1:2455/v1"),
        ("http://127.0.0.1:2455/v1/", "http://127.0.0.1:2455/v1"),
        ("http://127.0.0.1:2455", "http://127.0.0.1:2455/v1"),
        ("https://openrouter.ai/api/v1", "https://openrouter.ai/api/v1"),
        ("http://litellm:4000/", "http://litellm:4000/v1"),
    ],
)
def test_normalize_base_url(raw: str, expected: str) -> None:
    assert client.normalize_base_url(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "not-a-url", "ftp://x", "127.0.0.1:2455"],
)
def test_normalize_base_url_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValueError):
        client.normalize_base_url(raw)


def test_build_chat_completion_kwargs_includes_tools() -> None:
    payload = client.build_chat_completion_kwargs(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=128,
        temperature=0.5,
        top_p=1.0,
        tools=[{"type": "function", "function": {"name": "demo"}}],
    )
    assert payload["model"] == "gpt-4o-mini"
    assert payload["max_tokens"] == 128
    assert payload["temperature"] == 0.5
    assert payload["tool_choice"] == "auto"
    assert payload["tools"][0]["function"]["name"] == "demo"


def test_build_chat_completion_kwargs_for_codex_model() -> None:
    payload = client.build_chat_completion_kwargs(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=256,
        temperature=0.7,
        top_p=1.0,
    )
    assert payload["max_completion_tokens"] == 256
    assert "max_tokens" not in payload
    assert "temperature" not in payload
    assert "top_p" not in payload


def test_build_responses_kwargs_maps_messages() -> None:
    payload = client.build_responses_kwargs(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hello"},
        ],
        max_tokens=256,
        temperature=0.2,
        top_p=0.9,
    )
    assert payload["model"] == "gpt-4o-mini"
    assert payload["max_output_tokens"] == 256
    assert payload["temperature"] == 0.2
    assert payload["input"][0]["role"] == "system"
    assert payload["store"] is False
