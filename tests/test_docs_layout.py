"""Audience split for repository docs. This project is not hosted on uniskela.com."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
LINK = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"```[\s\S]*?```")
INLINE = re.compile(r"`[^`\n]*`")

LINK_ROOTS = [DOCS, ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "SECURITY.md", ROOT / "info.md"]


def _markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in LINK_ROOTS:
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("*.md")))
    return files


def _relative_links(path: Path) -> list[str]:
    text = INLINE.sub("", FENCE.sub("", path.read_text(encoding="utf-8")))
    return [match.group(1) for match in LINK.finditer(text)]


def test_audience_directories_exist_without_a_publish_manifest():
    assert (DOCS / "public").is_dir()
    assert (DOCS / "internal").is_dir()
    assert (DOCS / "agents").is_dir()
    assert not (DOCS / "manifest.json").exists()
    assert not (DOCS / "releases.md").exists()
    stray = [path.name for path in DOCS.glob("*.md") if path.name != "README.md"]
    assert stray == []
    assert (ROOT / "README.md").is_file()
    assert (ROOT / "AGENTS.md").is_file()


def test_root_guides_stay_canonical():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "](AGENTS.md)" in readme
    assert "](docs/public/releases.md)" in readme
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Releases (Release Please)" in agents
    assert "adhd-hub:project-agent:start" in agents
    notes = (DOCS / "agents" / "README.md").read_text(encoding="utf-8")
    assert "](../../AGENTS.md)" in notes
    assert "ADHD Hub continuity" not in notes
    assert "docs/manifest.json" in notes


def test_public_pages_do_not_link_at_unpublished_docs():
    public = DOCS / "public"
    for path in public.rglob("*.md"):
        for link in _relative_links(path):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                assert "uniskela.com/docs/" not in link
                continue
            target = (path.parent / link.split("#", 1)[0].split("?", 1)[0]).resolve()
            assert not target.is_relative_to(DOCS / "internal")
            assert not target.is_relative_to(DOCS / "agents")


def test_relative_markdown_links_resolve():
    missing: list[str] = []
    for path in _markdown_files():
        for link in _relative_links(path):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = link.split("#", 1)[0].split("?", 1)[0]
            if not relative:
                continue
            resolved = (path.parent / relative).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                missing.append(f"{path.relative_to(ROOT)} -> {link}")
                continue
            if not resolved.exists():
                missing.append(f"{path.relative_to(ROOT)} -> {link}")
    assert missing == []
