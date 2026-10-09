# Configuration

Secrets stay in the config entry. Never put API keys in `configuration.yaml`. Reporting guidance is in [SECURITY.md](../../SECURITY.md).

## Codex-LB example

| Field | Value |
| --- | --- |
| Base URL | `http://127.0.0.1:2455/v1` (or `http://<codex-lb-host>:2455/v1`) |
| API key | `sk-placeholder` if API key auth is disabled; otherwise a key from the Codex-LB dashboard |
| Conversation model | e.g. `gpt-5.3-codex` (use a model your Codex-LB instance exposes) |
| API protocol | Chat Completions (default) |

If Home Assistant runs in Docker or HA OS and Codex-LB is on the host, use a host-reachable address (not `127.0.0.1` from inside the container), for example `http://172.17.0.1:2455/v1` or your LAN IP.

## Generic OpenAI-compatible example

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

Platform behavior and backend limits are in [platforms and limits](reference.md).
