# Agent guide — Codex Custom Assist

Instructions for coding agents working in this repository.

## Releases (Release Please)

This repo uses [Release Please](https://github.com/googleapis/release-please) on pushes to `main`.

| File | Role |
|------|------|
| `.github/workflows/release-please.yml` | Runs Release Please on `main` |
| `release-please-config.json` | Release type + files to bump |
| `.release-please-manifest.json` | Last released version |
| `version.txt` | Simple releaser version source |
| `custom_components/codex_custom_assist/manifest.json` | HACS version (`$.version`, via `extra-files`) |
| `CHANGELOG.md` | Generated / updated by Release Please |

### Normal flow (agents + humans)

1. Open a **feature PR** into `main` with [Conventional Commits](https://www.conventionalcommits.org/) in the **merge commit or squashed commit message** (GitHub squash uses the PR title by default — set it carefully).
2. Merge the feature PR.
3. Release Please opens a **release PR** that bumps versions + `CHANGELOG.md`.
4. Merge the release PR → GitHub creates tag `vX.Y.Z` and the GitHub Release.

Commit prefixes that matter:

| Prefix | SemVer effect |
|--------|----------------|
| `fix:` | patch (`0.1.0` → `0.1.1`) |
| `feat:` | minor (`0.1.0` → `0.2.0`) |
| `feat!:` / `fix!:` / `BREAKING CHANGE:` | major (`0.1.0` → `1.0.0`) |
| `chore:`, `docs:`, `ci:`, `test:` | no release by themselves |

Do **not** hand-edit `manifest.json` / `version.txt` version numbers on feature PRs unless bootstrapping Release Please. Let the release PR own bumps.

### Target a specific version (`Release-As`)

To force the **next** release to a chosen SemVer, put this in the **commit body** that lands on `main`:

```text
feat: short summary of the change

Optional longer description.

Release-As: 0.1.0
```

### HACS note

HACS reads `custom_components/codex_custom_assist/manifest.json` → `version`. That field is updated by Release Please via `extra-files` in `release-please-config.json`.

## Merging and CODEOWNERS

- [`.github/CODEOWNERS`](.github/CODEOWNERS) assigns **@uniskela** as owner of the whole tree.
- Prefer PRs into `main` over direct pushes when branch protection is enabled.
