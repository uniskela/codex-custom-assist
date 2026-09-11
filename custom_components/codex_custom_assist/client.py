"""Extendable OpenAI-compatible client layer for Codex Custom Assist.

Backends are selected by configuration (`base_url`, `api_key`, protocol),
not by forking this integration. Codex-LB, LiteLLM, LocalAI, vLLM, OpenRouter,
and other Chat Completions–compatible servers share this client.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final, Literal, cast
from urllib.parse import urlparse, urlunparse

import openai
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    API_PROTOCOL_CHAT_COMPLETIONS,
    API_PROTOCOL_RESPONSES,
    LOGGER,
)

ApiProtocol = Literal["chat_completions", "responses"]

SUPPORTED_PROTOCOLS: Final = frozenset(
    {API_PROTOCOL_CHAT_COMPLETIONS, API_PROTOCOL_RESPONSES}
)

# Models that typically reject classic sampling / max_tokens on Chat Completions.
_REASONING_MODEL_PREFIXES: Final = (
    "o1",
    "o3",
    "o4",
    "gpt-5",
    "gpt-6",
    "codex",
)


def model_uses_completion_tokens(model: str) -> bool:
    """Return True when the model family prefers max_completion_tokens."""
    lowered = model.lower()
    return any(lowered.startswith(prefix) for prefix in _REASONING_MODEL_PREFIXES)


def model_supports_sampling_params(model: str) -> bool:
    """Return True when temperature/top_p are generally accepted."""
    return not model_uses_completion_tokens(model)


def normalize_base_url(base_url: str) -> str:
    """Normalize an OpenAI-compatible base URL.

    Accepts either `http://host:2455` or `http://host:2455/v1` and returns a
    URL suitable for the OpenAI Python SDK `base_url` (typically ending in `/v1`).
    """
    cleaned = base_url.strip().rstrip("/")
    if not cleaned:
        raise ValueError("base_url is required")

    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an absolute http(s) URL")

    path = parsed.path.rstrip("/")
    if path in {"", "/"}:
        path = "/v1"
    elif path == "/v1" or path.endswith("/v1"):
        pass
    else:
        # Preserve custom prefixes (e.g. /openai) and append /v1 when missing.
        path = f"{path}/v1"

    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", "")).rstrip("/")


def create_async_client(
    hass: HomeAssistant,
    *,
    api_key: str,
    base_url: str,
) -> openai.AsyncOpenAI:
    """Create an AsyncOpenAI client pointed at an OpenAI-compatible base URL."""
    normalized = normalize_base_url(base_url)
    LOGGER.debug("Creating OpenAI-compatible client for %s", normalized)
    return openai.AsyncOpenAI(
        api_key=api_key or "sk-placeholder",
        base_url=normalized,
        http_client=cast(Any, get_async_client(hass)),
    )


async def async_validate_provider(
    hass: HomeAssistant,
    *,
    api_key: str,
    base_url: str,
) -> list[str]:
    """Validate connectivity; return model ids when `/v1/models` is available.

    Some OpenAI-compatible proxies omit the models endpoint. In that case we
    probe with a lightweight request and return an empty model list rather than
    failing install — chat can still work.
    """
    client = create_async_client(hass, api_key=api_key, base_url=base_url)
    try:
        models = await client.models.list(timeout=15.0)
    except openai.NotFoundError:
        LOGGER.info(
            "Provider at %s has no /models endpoint; continuing without discovery",
            base_url,
        )
        return []
    except openai.APIStatusError as err:
        # 404/405/501 often mean "models not implemented" on local proxies.
        if err.status_code in {404, 405, 501}:
            LOGGER.info(
                "Provider at %s rejected /models (%s); continuing without discovery",
                base_url,
                err.status_code,
            )
            return []
        raise
    return [item.id for item in models.data if getattr(item, "id", None)]


def build_chat_completion_kwargs(
    *,
    model: str,
    messages: Sequence[dict[str, Any]],
    max_tokens: int,
    temperature: float,
    top_p: float,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build kwargs for chat.completions.create (widely supported)."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": list(messages),
    }

    if model_uses_completion_tokens(model):
        # GPT-5 / Codex / o-series style APIs.
        payload["max_completion_tokens"] = max_tokens
    else:
        payload["max_tokens"] = max_tokens

    if model_supports_sampling_params(model):
        payload["temperature"] = temperature
        payload["top_p"] = top_p

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    return payload


def build_responses_kwargs(
    *,
    model: str,
    messages: Sequence[dict[str, Any]],
    max_tokens: int,
    temperature: float,
    top_p: float,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build kwargs for responses.create (OpenAI Responses–compatible proxies)."""
    input_items: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "tool":
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": message.get("tool_call_id", ""),
                    "output": content if isinstance(content, str) else str(content),
                }
            )
            continue
        if role == "assistant" and message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                function = tool_call.get("function", {})
                input_items.append(
                    {
                        "type": "function_call",
                        "call_id": tool_call.get("id", ""),
                        "name": function.get("name", ""),
                        "arguments": function.get("arguments", "{}"),
                    }
                )
            if content:
                input_items.append(
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": content,
                    }
                )
            continue
        input_items.append(
            {
                "type": "message",
                "role": role,
                "content": content if isinstance(content, str) else str(content),
            }
        )

    payload: dict[str, Any] = {
        "model": model,
        "input": input_items,
        "max_output_tokens": max_tokens,
        "store": False,
    }
    if model_supports_sampling_params(model):
        payload["temperature"] = temperature
        payload["top_p"] = top_p
    if tools:
        payload["tools"] = [
            {
                "type": "function",
                "name": tool["function"]["name"],
                "description": tool["function"].get("description"),
                "parameters": tool["function"].get("parameters", {}),
                "strict": False,
            }
            for tool in tools
            if tool.get("type") == "function" and "function" in tool
        ]
    return payload
