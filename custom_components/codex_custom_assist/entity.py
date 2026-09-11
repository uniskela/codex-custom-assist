"""Shared entity helpers for Codex Custom Assist."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from . import CodexCustomAssistConfigEntry
from .const import (
    CONF_BASE_URL,
    CONF_CHAT_MODEL,
    DEFAULT_NAME,
    DOMAIN,
    RECOMMENDED_CHAT_MODEL,
)


class CodexCustomAssistEntity(Entity):
    """Base entity sharing one service device per config entry."""

    _attr_has_entity_name = True
    _attr_name: str | None = None

    def __init__(
        self,
        entry: CodexCustomAssistConfigEntry,
        *,
        unique_id: str,
        name: str | None = None,
    ) -> None:
        """Initialize shared entity fields."""
        self.entry = entry
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or DEFAULT_NAME,
            manufacturer="Codex Custom Assist",
            model=entry.options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
            entry_type=dr.DeviceEntryType.SERVICE,
            configuration_url=entry.data.get(CONF_BASE_URL),
        )

    def _option(self, key: str, default: Any = None) -> Any:
        """Read an option with fallback."""
        return self.entry.options.get(key, default)
