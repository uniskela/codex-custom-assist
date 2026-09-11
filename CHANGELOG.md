# Changelog

## [0.3.0](https://github.com/uniskela/codex-custom-assist/compare/v0.2.0...v0.3.0) (2026-09-11)


### Features

* add AI Task platform with structured schema output ([bad9cd0](https://github.com/uniskela/codex-custom-assist/commit/bad9cd04765ae6a2bd8a0f9b5858c42a515e9249))
* add shared entity base and multi-platform setup ([959fbdf](https://github.com/uniskela/codex-custom-assist/commit/959fbdf7c510a255ded2f737285ef3b8bd444117))
* add Speech-to-text platform ([c54f300](https://github.com/uniskela/codex-custom-assist/commit/c54f300d9aa60abee8d2ac73394018ba204a8610))
* add STT/TTS/AI Task options strings and translations ([aeacfcc](https://github.com/uniskela/codex-custom-assist/commit/aeacfcc71eef3b953ce5ae3ebdd5ae97f1d21e97))
* add STT/TTS/AI Task platform modules (part 1) ([731b29e](https://github.com/uniskela/codex-custom-assist/commit/731b29e4f1891922ccc5110d28eec3f3e3576c82))
* add Text-to-speech platform with instructions soft-retry ([7e07f95](https://github.com/uniskela/codex-custom-assist/commit/7e07f95822640e19376f3bda63758ab55612eaa4))
* bump to v0.2.0 metadata and docs for STT/TTS/AI Task ([83036b3](https://github.com/uniskela/codex-custom-assist/commit/83036b3d11b75e7ea33ca8cbc2d8513047b617dd))
* expand constants for STT/TTS/AI Task options ([ce04bfd](https://github.com/uniskela/codex-custom-assist/commit/ce04bfdb0e02b861fdc58a0cc337c6a9999d530d))
* expand options flow for STT/TTS/AI Task ([bacf1a9](https://github.com/uniskela/codex-custom-assist/commit/bacf1a9d59af5fc720bdc6251acf1777014e9c8e))
* STT, TTS, and AI Task platforms (v0.2.0) ([2b1f4b3](https://github.com/uniskela/codex-custom-assist/commit/2b1f4b3e3ad50c7681ad8c12d1ea05c723edf0ee))


### Bug Fixes

* use shared entity base; keep conversation name=None ([f3eab41](https://github.com/uniskela/codex-custom-assist/commit/f3eab419588d246beccd068a64ac329d5afd1a70))

## [0.2.0](https://github.com/uniskela/codex-custom-assist/releases/tag/v0.2.0) (2026-09-11)

### Features

* add Speech-to-text, Text-to-speech, and AI Task platforms alongside Conversation (OpenAI integration entity parity)
* options for per-platform models, TTS voice/speed, and STT/TTS prompts
* soft-fail with clear errors when a backend omits `/v1/audio/*` endpoints

## [0.1.0](https://github.com/uniskela/codex-custom-assist/releases/tag/v0.1.0) (2026-09-11)

### Features

* initial Codex Custom Assist conversation integration for OpenAI-compatible APIs (Codex-LB and others)
