"""Conversation agent for Codex Custom Assist."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Literal

import openai
import voluptuous as vol
from homeassistant.components import conversation
from homeassistant.const import CONF_LLM_HASS_API, CONF_PROMPT, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.json import json_dumps

from . import CodexCustomAssistConfigEntry
from .client import build_chat_completion_kwargs, build_responses_kwargs
from .const import (
    API_PROTOCOL_RESPONSES,
    CONF_API_PROTOCOL,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DOMAIN,
    LOGGER,
    MAX_TOOL_ITERATIONS,
    RECOMMENDED_API_PROTOCOL,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)
from .entity import CodexCustomAssistEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexCustomAssistConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Codex Custom Assist conversation entity."""
    async_add_entities([CodexCustomAssistConversationEntity(config_entry)])


def _schema_to_openai(
    schema: vol.Schema, custom_serializer: Callable[[Any], Any] | None
) -> dict[str, Any]:
    """Convert a voluptuous schema to a JSON Schema object for tools."""
    serializer = custom_serializer or llm.selector_serializer
    try:
        from probatio import to_openapi  # type: ignore[import-not-found]

        result = to_openapi(schema, custom_serializer=serializer)
        if isinstance(result, dict):
            return result
    except Exception:  # noqa: BLE001
        pass

    try:
        from voluptuous_openapi import convert as openapi_convert

        result = openapi_convert(schema, custom_serializer=serializer)
        if isinstance(result, dict):
            return result
    except Exception:  # noqa: BLE001
        pass

    try:
        import voluptuous_serialize

        result = voluptuous_serialize.convert(schema, custom_serializer=serializer)
        if isinstance(result, dict):
            return result
    except Exception:  # noqa: BLE001
        LOGGER.debug("Falling back to permissive tool schema", exc_info=True)

    return {"type": "object", "properties": {}, "additionalProperties": True}


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> dict[str, Any]:
    """Format an HA LLM tool for Chat Completions function calling."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": _schema_to_openai(tool.parameters, custom_serializer),
        },
    }


def _message_content_to_text(content: Any) -> str:
    """Flatten chat content parts to text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") in {"text", "input_text"}:
                parts.append(str(part.get("text", "")))
        return "\n".join(p for p in parts if p)
    return str(content)


def _chat_log_to_messages(chat_log: conversation.ChatLog) -> list[dict[str, Any]]:
    """Convert an HA ChatLog into OpenAI chat messages."""
    messages: list[dict[str, Any]] = []

    for content in chat_log.content:
        if isinstance(content, conversation.SystemContent):
            text = _message_content_to_text(content.content)
            if text:
                messages.append({"role": "system", "content": text})
            continue

        if isinstance(content, conversation.UserContent):
            messages.append(
                {
                    "role": "user",
                    "content": _message_content_to_text(content.content),
                }
            )
            continue

        if isinstance(content, conversation.AssistantContent):
            message: dict[str, Any] = {
                "role": "assistant",
                "content": _message_content_to_text(content.content) or None,
            }
            if content.tool_calls:
                message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.tool_name,
                            "arguments": json_dumps(tool_call.tool_args),
                        },
                    }
                    for tool_call in content.tool_calls
                ]
            messages.append(message)
            continue

        if isinstance(content, conversation.ToolResultContent):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": content.tool_call_id,
                    "content": json_dumps(content.tool_result),
                }
            )
            continue

        LOGGER.debug("Skipping unsupported chat content: %s", type(content))

    return messages


def _extract_responses_output(response: Any) -> tuple[str | None, list[dict[str, Any]]]:
    """Extract assistant text and function calls from a Responses API result."""
    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []

    for item in getattr(response, "output", []) or []:
        item_type = getattr(item, "type", None)
        if item_type == "message":
            for part in getattr(item, "content", []) or []:
                if getattr(part, "type", None) in {"output_text", "text"}:
                    text_parts.append(getattr(part, "text", "") or "")
        elif item_type == "function_call":
            tool_calls.append(
                {
                    "id": getattr(item, "call_id", "") or getattr(item, "id", ""),
                    "type": "function",
                    "function": {
                        "name": getattr(item, "name", ""),
                        "arguments": getattr(item, "arguments", "{}") or "{}",
                    },
                }
            )

    text = "".join(text_parts).strip() or None
    return text, tool_calls


class CodexCustomAssistConversationEntity(
    CodexCustomAssistEntity,
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """Codex Custom Assist conversation agent."""

    _attr_supports_streaming = False

    def __init__(self, entry: CodexCustomAssistConfigEntry) -> None:
        """Initialize the agent."""
        # Keep unique_id = entry_id for upgrades from 0.1.0.
        # name=None + has_entity_name → friendly name is the device title (0.1.0).
        super().__init__(
            entry,
            unique_id=entry.entry_id,
            name=None,
        )
        if entry.options.get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """Register as conversation agent."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister conversation agent."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process user input via ChatLog (Home Assistant Assist path)."""
        options = self.entry.options

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                options.get(CONF_LLM_HASS_API),
                options.get(CONF_PROMPT),
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        await self._async_handle_chat_log(chat_log)
        return conversation.async_get_result_from_chat_log(user_input, chat_log)

    async def _async_handle_chat_log(self, chat_log: conversation.ChatLog) -> None:
        """Call the configured OpenAI-compatible API against the chat log."""
        options = self.entry.options
        client: openai.AsyncOpenAI = self.entry.runtime_data
        model = options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL)
        protocol = options.get(CONF_API_PROTOCOL, RECOMMENDED_API_PROTOCOL)
        max_tokens = int(options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS))
        temperature = float(options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE))
        top_p = float(options.get(CONF_TOP_P, RECOMMENDED_TOP_P))

        tools: list[dict[str, Any]] | None = None
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        for _iteration in range(MAX_TOOL_ITERATIONS):
            messages = _chat_log_to_messages(chat_log)
            try:
                if protocol == API_PROTOCOL_RESPONSES:
                    payload = build_responses_kwargs(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        tools=tools,
                    )
                    response = await client.responses.create(**payload)
                    text, raw_tool_calls = _extract_responses_output(response)
                else:
                    payload = build_chat_completion_kwargs(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        tools=tools,
                    )
                    response = await client.chat.completions.create(**payload)
                    choices = getattr(response, "choices", None) or []
                    if not choices:
                        raise HomeAssistantError(
                            "OpenAI-compatible API returned no choices"
                        )
                    message = choices[0].message
                    text = message.content
                    raw_tool_calls = []
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            raw_tool_calls.append(
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                        or "{}",
                                    },
                                }
                            )
            except openai.AuthenticationError as err:
                self.entry.async_start_reauth(self.hass)
                raise HomeAssistantError(
                    f"Authentication failed for Codex Custom Assist provider: {err}"
                ) from err
            except openai.OpenAIError as err:
                raise HomeAssistantError(
                    f"Error talking to OpenAI-compatible API: {err}"
                ) from err

            tool_inputs: list[llm.ToolInput] | None = None
            if raw_tool_calls:
                tool_inputs = []
                for tool_call in raw_tool_calls:
                    function = tool_call["function"]
                    try:
                        tool_args = json.loads(function["arguments"] or "{}")
                    except json.JSONDecodeError as err:
                        raise HomeAssistantError(
                            f"Model returned invalid tool arguments JSON: {err}"
                        ) from err
                    if not isinstance(tool_args, dict):
                        raise HomeAssistantError(
                            "Model returned non-object tool arguments"
                        )
                    tool_inputs.append(
                        llm.ToolInput(
                            id=tool_call["id"],
                            tool_name=function["name"],
                            tool_args=tool_args,
                        )
                    )

            async for _tool_result in chat_log.async_add_assistant_content(
                conversation.AssistantContent(
                    agent_id=self.entity_id,
                    content=text,
                    tool_calls=tool_inputs,
                )
            ):
                pass

            if not tool_inputs:
                return

        raise HomeAssistantError("Codex Custom Assist exceeded the maximum tool iterations")
