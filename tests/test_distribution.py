"""Staged Markdown distribution checks, not external client execution evidence."""

import json
import re
import shutil
from pathlib import Path

import pytest

from tests.test_agent_native_skill import check_local_links

ROOT = Path(__file__).parents[1]
CANONICAL = Path(".github/skills/proof-readiness")
ASSETS = {
    "SKILL.md",
    "references/index.md",
    "references/kani.md",
    "references/verus.md",
    "references/cbmc.md",
    "references/tlc.md",
    "references/dafny.md",
    "templates/assessment.md",
    "examples/assessments.md",
    "LICENSE",
}


def check_distribution(folder):
    """Only self-contained guidance and its unchanged standalone MIT notice."""
    assert not any(path.is_symlink() for path in folder.rglob("*"))
    assert {path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file()} == ASSETS
    assert (folder / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
    check_local_links(folder)


@pytest.fixture
def staged_plugin(tmp_path):
    """Package only manifests, license, and guidance; no src, engine, or venv."""
    stage = tmp_path / "plugin"
    shutil.copytree(ROOT / ".claude-plugin", stage / ".claude-plugin")
    shutil.copyfile(ROOT / "LICENSE", stage / "LICENSE")
    shutil.copytree(ROOT / CANONICAL, stage / CANONICAL)
    return stage


def test_plugin_resolves_single_canonical_skill_without_engine(staged_plugin):
    stage = staged_plugin
    marketplace = json.loads((stage / ".claude-plugin/marketplace.json").read_text())
    assert marketplace["name"] == "spec-proof-consultant"
    assert marketplace["owner"] == {"name": "jameshuangdevelop"}
    assert marketplace["plugins"] == [{"name": "proof-readiness", "source": "./"}]
    plugin_root = (stage / marketplace["plugins"][0]["source"]).resolve()
    assert plugin_root == stage.resolve()
    plugin = json.loads((plugin_root / ".claude-plugin/plugin.json").read_text())
    assert set(plugin) == {"name", "version", "description", "license", "skills"}
    assert plugin["name"] == marketplace["plugins"][0]["name"]
    assert plugin["license"] == "MIT"
    assert (plugin_root / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
    assert plugin["skills"] == ["./.github/skills/"]
    container = (plugin_root / plugin["skills"][0]).resolve()
    assert container.is_relative_to(plugin_root)
    discovered = list(container.glob("*/SKILL.md"))
    assert discovered == [plugin_root / CANONICAL / "SKILL.md"]
    frontmatter = discovered[0].read_text().split("---", 2)[1]
    assert re.search(r"^name: (.+)$", frontmatter, re.MULTILINE)[1] == plugin["name"]
    assert re.search(r'^  version: "([^"]+)"$', frontmatter, re.MULTILINE)[1] == plugin["version"]
    check_distribution(discovered[0].parent)
    expected = {CANONICAL / asset for asset in ASSETS} | {
        Path(".claude-plugin/plugin.json"),
        Path(".claude-plugin/marketplace.json"),
        Path("LICENSE"),
    }
    assert {p.relative_to(stage) for p in stage.rglob("*") if p.is_file()} == expected


def test_whole_folder_relocates_with_license_and_byte_identical_assets(staged_plugin, tmp_path):
    installed = tmp_path / "unrelated-workspace/skills/proof-readiness"
    shutil.copytree(staged_plugin / CANONICAL, installed)
    shutil.rmtree(staged_plugin)
    check_distribution(installed)
    for asset in ASSETS:
        assert (installed / asset).read_bytes() == (ROOT / CANONICAL / asset).read_bytes()


@pytest.mark.parametrize(
    "damage", ["license-missing", "license-changed", "guide-missing", "escaping-link", "skill-only"]
)
def test_distribution_rejects_incomplete_or_nonportable_copies(staged_plugin, damage):
    folder = staged_plugin / CANONICAL
    if damage == "license-missing":
        (folder / "LICENSE").unlink()
    elif damage == "license-changed":
        (folder / "LICENSE").write_text("MIT without the required notice")
    elif damage == "guide-missing":
        (folder / "references/kani.md").unlink()
    elif damage == "escaping-link":
        (folder / "SKILL.md").write_text("[outside](../../../LICENSE)")
    else:
        for path in folder.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            elif path.name != "SKILL.md":
                path.unlink()
    with pytest.raises(AssertionError):
        check_distribution(folder)
