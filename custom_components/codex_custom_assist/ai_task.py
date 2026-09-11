"""AI Task support for Codex Custom Assist."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAIError

from homeassistant.components import ai_task, conversation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.json import json_loads

from . import CodexCustomAssistConfigEntry
from .client import build_chat_completion_kwargs, build_responses_kwargs
from .const import (
    API_PROTOCOL_RESPONSES,
    CONF_AI_TASK_MODEL,
    CONF_API_PROTOCOL,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    RECOMMENDED_API_PROTOCOL,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)
from .conversation import _chat_log_to_messages, _schema_to_openai
from .entity import CodexCustomAssistEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

AI_TASK_SYSTEM_PROMPT = (
    "You are a Home Assistant AI assistant that helps users with tasks. "
    "Follow the user's instructions precisely. "
    "When asked to generate structured data, respond with valid JSON only."
)


def strip_markdown_json_fence(text: str) -> str:
    """Remove a leading ``` / ```json fence if the model wrapped JSON."""
    clean = text.strip()
    if not clean.startswith("```"):
        return clean
    lines = clean.split("\n")
    if lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return "\n".join(lines[1:]).strip()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexCustomAssistConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AI Task entity."""
    async_add_entities([CodexCustomAssistAITaskEntity(config_entry)])


class CodexCustomAssistAITaskEntity(ai_task.AITaskEntity, CodexCustomAssistEntity):
    """OpenAI-compatible AI Task entity (GENERATE_DATA)."""

    _attr_supported_features = ai_task.AITaskEntityFeature.GENERATE_DATA

    def __init__(self, entry: CodexCustomAssistConfigEntry) -> None:
        """Initialize AI Task entity."""
        # Short name with has_entity_name=True → "{title} AI Task".
        super().__init__(
            entry,
            unique_id=f"{entry.entry_id}_ai_task",
            name="AI Task",
        )

    def _structure_prompt_block(self, structure: Any) -> str:
        """Serialize task.structure into prompt text the model can follow."""
        schema_obj = _schema_to_openai(structure, None)
        schema_json = json.dumps(schema_obj, ensure_ascii=False)
        return (
            "Respond with ONLY a valid JSON object matching this JSON Schema. "
            "Do not wrap it in markdown.\n"
            f"{schema_json}"
        )

    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Generate text or structured JSON via chat completions / responses."""
        options = self.entry.options
        client = self.entry.runtime_data
        model = options.get(
            CONF_AI_TASK_MODEL,
            options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
        )
        protocol = options.get(CONF_API_PROTOCOL, RECOMMENDED_API_PROTOCOL)
        max_tokens = int(options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS))
        temperature = float(options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE))
        top_p = float(options.get(CONF_TOP_P, RECOMMENDED_TOP_P))

        messages = _chat_log_to_messages(chat_log)
        structure_block = (
            self._structure_prompt_block(task.structure) if task.structure else ""
        )
        if not any(message.get("role") == "system" for message in messages):
            system_prompt = AI_TASK_SYSTEM_PROMPT
            if structure_block:
                system_prompt = f"{system_prompt}\n\n{structure_block}"
            messages.insert(0, {"role": "system", "content": system_prompt})
        elif structure_block and messages and messages[0].get("role") == "system":
            messages[0]["content"] = (
                f"{messages[0].get('content', '')}\n\n{structure_block}"
            ).strip()

        try:
            if protocol == API_PROTOCOL_RESPONSES:
                payload = build_responses_kwargs(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )
                if task.structure:
                    # Best-effort json_object mode when Responses backends support it.
                    payload["text"] = {"format": {"type": "json_object"}}
                try:
                    response = await client.responses.create(**payload)
                except OpenAIError:
                    payload.pop("text", None)
                    response = await client.responses.create(**payload)
                text_parts: list[str] = []
                for item in getattr(response, "output", []) or []:
                    if getattr(item, "type", None) != "message":
                        continue
                    for part in getattr(item, "content", []) or []:
                        if getattr(part, "type", None) in {"output_text", "text"}:
                            text_parts.append(getattr(part, "text", "") or "")
                text = "".join(text_parts).strip()
            else:
                payload = build_chat_completion_kwargs(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )
                if task.structure:
                    # Prefer json_schema when the backend accepts it; fall back.
                    schema_obj = _schema_to_openai(task.structure, None)
                    payload["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "ai_task_result",
                            "strict": False,
                            "schema": schema_obj,
                        },
                    }
                try:
                    response = await client.chat.completions.create(**payload)
                except OpenAIError:
                    if task.structure and "response_format" in payload:
                        payload["response_format"] = {"type": "json_object"}
                        try:
                            response = await client.chat.completions.create(**payload)
                        except OpenAIError:
                            payload.pop("response_format", None)
                            response = await client.chat.completions.create(**payload)
                    else:
                        raise
                choices = getattr(response, "choices", None) or []
                if not choices:
                    raise HomeAssistantError(
                        "OpenAI-compatible API returned no choices for AI Task"
                    )
                text = (choices[0].message.content or "").strip()
        except OpenAIError as err:
            _LOGGER.exception("AI Task generation failed (model=%s)", model)
            raise HomeAssistantError(
                f"AI Task failed on this OpenAI-compatible backend: {err}"
            ) from err

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=self.entity_id,
                content=text,
            )
        )

        if not task.structure:
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=text,
            )

        data: Any
        try:
            data = json_loads(strip_markdown_json_fence(text))
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to parse AI Task JSON: %s (%s)", err, text[:200])
            raise HomeAssistantError(
                "Error parsing structured AI Task response as JSON"
            ) from err

        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=data,
        )
