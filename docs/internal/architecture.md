# Architecture

- Entry **data** stores secrets and connection settings: `base_url`, `api_key`
- Entry **options** store platform settings: models, prompts, voice, sampling, protocol
- `custom_components/codex_custom_assist/client.py` owns URL normalization and chat/responses payload builders so new backends stay config-only

User setup is in [configuration](../public/configuration.md).
