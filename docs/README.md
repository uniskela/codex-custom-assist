# Documentation layout

| Audience | Path | Publication |
| --- | --- | --- |
| Home Assistant users | `public/` | Repository only |
| Maintainers | `internal/` | Repository only |
| Coding agents | `agents/` | Repository only |

Root [README.md](../README.md) stays the HACS-rendered guide (`render_readme` in `hacs.json`). Root [AGENTS.md](../AGENTS.md) stays the canonical agent guide. `agents/` points at that file and does not replace it.

This repository is not a uniskela.com documentation source. Do not add `docs/manifest.json` or hosted pages for it.

“Internal” is a publication boundary, not confidentiality: these files stay visible on GitHub. Do not put secrets in any documentation tree.

When setup or configuration changes, update the README and the matching page under `public/` together.
