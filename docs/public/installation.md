# Installation

## Requirements

- Home Assistant **2025.1+** (AI Task and ChatLog conversation entity APIs)
- Network reachability from Home Assistant to your API host

## HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=uniskela&repository=codex-custom-assist&category=integration)

1. Click the badge above, **or** in HACS add custom repository `https://github.com/uniskela/codex-custom-assist` (type: Integration), **or** copy `custom_components/codex_custom_assist` into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.
3. **Settings → Devices & services → Add integration → Codex Custom Assist**.
4. **Settings → Voice assistants** → edit an assistant → set **Conversation agent** (and optionally STT/TTS) to Codex Custom Assist.

Continue with [configuration](configuration.md).
