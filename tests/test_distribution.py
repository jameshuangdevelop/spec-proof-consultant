"""Offline distribution checks; never invoke clients or external installers."""

import json
import re
import shutil
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]


def assert_local_links_contained(directory):
    """Local Markdown dependencies must survive copying only the skill bundle."""
    for document in directory.rglob("*.md"):
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", document.read_text()):
            url = urlsplit(target)
            assert url.scheme != "file", (document, target)
            if url.scheme or url.netloc or not url.path:
                continue
            linked = (document.parent / unquote(url.path)).resolve()
            assert linked.is_relative_to(directory.resolve()), (document, target)
            assert linked.is_file(), (document, target)


def test_root_marketplace_and_plugin_resolve_one_canonical_skill():
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert marketplace["name"] == "spec-consultant"
    assert marketplace["owner"]["name"] == "Spec Consultant"
    assert len(marketplace["plugins"]) == 1
    entry = marketplace["plugins"][0]
    assert entry["source"] == "./"
    plugin_root = (ROOT / entry["source"]).resolve()
    plugin = json.loads((plugin_root / ".claude-plugin/plugin.json").read_text())
    assert plugin["name"] == entry["name"] == "proof-readiness"
    # No executable components or extra distribution surfaces.
    assert set(plugin) == {"name", "version", "description", "skills"}
    assert plugin["description"].strip()
    assert plugin["skills"] == ["./.github/skills/proof-readiness"]
    skill_dir = plugin_root / plugin["skills"][0]
    assert skill_dir.resolve().is_relative_to(plugin_root)
    assert skill_dir.is_dir() and not skill_dir.is_symlink()
    assert not any(path.is_symlink() for path in skill_dir.rglob("*"))
    assert list(ROOT.rglob("SKILL.md")) == [skill_dir / "SKILL.md"]

    text = (skill_dir / "SKILL.md").read_text()
    frontmatter = text.split("---", 2)[1]
    assert re.search(r"^name: proof-readiness$", frontmatter, re.MULTILINE)
    skill_version = re.search(r'^  version: "([^"]+)"$', frontmatter, re.MULTILINE).group(1)
    runtime = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert plugin["version"] == skill_version == runtime["project"]["version"]


def test_skill_can_relocate_without_repository_files(tmp_path):
    destination = tmp_path / "arbitrary-agent" / "skills" / "proof-readiness"
    shutil.copytree(ROOT / ".github/skills/proof-readiness", destination)
    assert (destination / "SKILL.md").is_file()
    assert_local_links_contained(destination)


@pytest.mark.parametrize(
    "target", ["../README.md", "/outside/skill.md", "missing.md", "%2e%2e/README.md", "file:///outside/skill.md"]
)
def test_bundle_link_check_rejects_escape_and_missing_dependencies(tmp_path, target):
    # A regression in closure checking must not silently endorse outside links.
    bundle = tmp_path / "skill"
    bundle.mkdir()
    (tmp_path / "README.md").write_text("outside the install bundle")
    (bundle / "SKILL.md").write_text(f"[required instructions]({target})")
    with pytest.raises(AssertionError):
        assert_local_links_contained(bundle)


def test_bundle_link_check_accepts_bundled_and_external_references(tmp_path):
    (tmp_path / "notes.md").write_text("bundled notes")
    (tmp_path / "SKILL.md").write_text(
        "[notes](notes.md#details) [section](#workflow) [spec](https://agentskills.io/specification)"
    )
    assert_local_links_contained(tmp_path)
