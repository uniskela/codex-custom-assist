# Security Policy

## Reporting

If you find a security issue in Codex Custom Assist, open a **private** GitHub security advisory on [uniskela/codex-custom-assist](https://github.com/uniskela/codex-custom-assist) or email the maintainer. Do not file a public issue with live API keys or Home Assistant `.storage` config entries.

## What this integration stores

- **API key** and **base URL** for the configured OpenAI-compatible provider in the Home Assistant config entry.
- Conversation options (model, prompt, sampling) in the config entry options.

Secrets are never written to `configuration.yaml` by this integration.

## Operator guidance

- Prefer LAN/VPN endpoints for self-hosted proxies such as Codex-LB.
- Treat API keys like any other cloud credential; rotate if leaked.
- Do not commit HA `.storage` config entries, `.env` files, or provider keys to git.
