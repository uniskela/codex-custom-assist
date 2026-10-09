# Releases

Codex Custom Assist uses [Release Please](https://github.com/googleapis/release-please) to bump versions, update `CHANGELOG.md`, and publish GitHub releases.

## Quick reference

1. Merge feature work to `main` with `feat:` / `fix:` (or `Release-As: X.Y.Z` in the commit body).
2. Merge the Release Please PR that appears.
3. Tag `vX.Y.Z` and the GitHub Release are created automatically.

Version sources bumped together: `version.txt` and `custom_components/codex_custom_assist/manifest.json`.
