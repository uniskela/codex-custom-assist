# Codex Custom Assist

Home Assistant custom integration for **OpenAI-compatible** APIs. One config entry exposes the same entity types as Home Assistant’s built-in OpenAI / ChatGPT integration:

- **Conversation** agent
- **Speech-to-text (STT)**
- **Text-to-speech (TTS)**
- **AI Task**

It fills the gap left by core [OpenAI Conversation](https://www.home-assistant.io/integrations/openai_conversation/) by letting you set a configurable `base_url` + `api_key`.

> **Disclaimer:** This project is a community Home Assistant custom component. It is **not affiliated with, endorsed by, or associated with** ChatGPT, Codex, OpenAI, or any related trademarks. “Codex” / “OpenAI-compatible” here only describe API compatibility.

Primary example: [Codex-LB](https://github.com/soju06/codex-lb) (`http://127.0.0.1:2455/v1`). Other backends (LiteLLM, LocalAI, vLLM, OpenRouter, …) are configuration — not forks.

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/uniskela/codex-custom-assist/actions/workflows/validate.yml/badge.svg)](https://github.com/uniskela/codex-custom-assist/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/uniskela/codex-custom-assist)](LICENSE)

## Features

- Config flow: API base URL, API key, conversation model
- Options flow: per-platform models (conversation / STT / TTS / AI Task), voice, speed, prompts, Assist control, sampling, API protocol
- Four entities under one service device (parity with the OpenAI integration entity list)
- Soft-fail with clear errors when a backend omits audio endpoints
- Extendable provider client (`client.py`) shared by all OpenAI-compatible backends
- Protocol choice for chat/AI Task:
  - **Chat Completions** (`/v1/chat/completions`) — default, widest compatibility
  - **Responses** (`/v1/responses`) — for proxies that implement the Responses API

## Platforms

| Entity | Endpoint(s) | Notes |
| --- | --- | --- |
| Conversation | Chat Completions or Responses | Assist agent; optional HA tool control |
| STT | `/v1/audio/transcriptions` | Default model `whisper-1` |
| TTS | `/v1/audio/speech` | Default model `tts-1`, voice `alloy`; clear error if unsupported |
| AI Task | Chat Completions or Responses | `GENERATE_DATA` (structured JSON / text). No image generation |

### Codex-LB limitations

- **Conversation / AI Task:** work when the LB exposes Chat Completions (typical).
- **STT:** works if the LB proxies `/v1/audio/transcriptions` to a Whisper-compatible model.
- **TTS:** often **not** implemented on Codex-LB; the TTS entity remains available and raises a clear Home Assistant error when `/v1/audio/speech` is missing.
- **AI Task:** text/JSON data generation only — not OpenAI image generation.

## Requirements

- Home Assistant **2025.1+** (AI Task + ChatLog conversation entity APIs)
- Network reachability from Home Assistant to your API host

## Install (HACS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=uniskela&repository=codex-custom-assist&category=integration)

1. Click the badge above, **or** in HACS add custom repository `https://github.com/uniskela/codex-custom-assist` (type: Integration), **or** copy `custom_components/codex_custom_assist` into your HA `config/custom_components/` folder.
2. Restart Home Assistant.
3. **Settings → Devices & services → Add integration → Codex Custom Assist**.
4. **Settings → Voice assistants** → edit an assistant → set **Conversation agent** (and optionally STT/TTS) to Codex Custom Assist.

## Configure

### Codex-LB example

| Field | Value |
| --- | --- |
| Base URL | `http://127.0.0.1:2455/v1` (or `http://<codex-lb-host>:2455/v1`) |
| API key | `sk-placeholder` if API key auth is disabled; otherwise a key from the Codex-LB dashboard |
| Conversation model | e.g. `gpt-5.3-codex` (use a model your Codex-LB instance exposes) |
| API protocol | Chat Completions (default) |

If Home Assistant runs in Docker/HA OS and Codex-LB is on the host, use a host-reachable address (not `127.0.0.1` from inside the container), e.g. `http://172.17.0.1:2455/v1` or your LAN IP.

### Generic OpenAI-compatible example

| Field | Value |
| --- | --- |
| Base URL | `http://litellm:4000/v1` / `http://localai:8080/v1` / `https://openrouter.ai/api/v1` |
| API key | Provider key (required for most cloud gateways) |
| Conversation model | Provider model id |
| API protocol | Chat Completions unless the provider documents Responses support |

## Options

- **Instructions** / **Control Home Assistant** / conversation sampling / API protocol
- **STT model** + optional transcription prompt
- **TTS model**, **voice**, **speed**, optional speaking instructions
- **AI Task model** (defaults to the conversation model)

## Architecture notes

- Entry **data** stores secrets/connection: `base_url`, `api_key`
- Entry **options** store platform settings: models, prompts, voice, sampling, protocol
- `custom_components/codex_custom_assist/client.py` owns URL normalization and chat/responses payload builders so new backends stay config-only

## Security

- Never put API keys in `configuration.yaml`.
- Secrets stay in the config entry.
- See [SECURITY.md](SECURITY.md) for reporting guidance.

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

Releases are automated with [Release Please](https://github.com/googleapis/release-please). Prefer [Conventional Commits](https://www.conventionalcommits.org/) on `main` (`feat:`, `fix:`, etc.). After merge, Release Please opens a release PR that bumps `version.txt`, `custom_components/codex_custom_assist/manifest.json`, and `CHANGELOG.md`, then tags/publishes the GitHub release when that PR merges.

See [AGENTS.md](AGENTS.md) and [docs/releases.md](docs/releases.md).

## License

MIT
