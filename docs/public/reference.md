# Platforms and limits

One config entry exposes the same entity types as Home Assistant’s built-in OpenAI / ChatGPT integration.

| Entity | Endpoint(s) | Notes |
| --- | --- | --- |
| Conversation | Chat Completions or Responses | Assist agent; optional Home Assistant tool control |
| STT | `/v1/audio/transcriptions` | Default model `whisper-1` |
| TTS | `/v1/audio/speech` | Default model `tts-1`, voice `alloy`; clear error if unsupported |
| AI Task | Chat Completions or Responses | `GENERATE_DATA` (structured JSON / text). No image generation |

Protocol choice for chat and AI Task:

- **Chat Completions** (`/v1/chat/completions`) — default, widest compatibility
- **Responses** (`/v1/responses`) — for proxies that implement the Responses API

The integration soft-fails with a clear error when a backend omits an audio endpoint.

## Codex-LB limitations

Primary example backend: [Codex-LB](https://github.com/soju06/codex-lb). Other backends (LiteLLM, LocalAI, vLLM, OpenRouter, and similar) are configuration, not forks.

- **Conversation / AI Task:** work when the load balancer exposes Chat Completions (typical).
- **STT:** works if the load balancer proxies `/v1/audio/transcriptions` to a Whisper-compatible model.
- **TTS:** often **not** implemented on Codex-LB. The TTS entity remains available and raises a clear Home Assistant error when `/v1/audio/speech` is missing.
- **AI Task:** text/JSON data generation only — not OpenAI image generation.
