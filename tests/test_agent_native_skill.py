"""Mechanical asset/contract regressions, not evaluation of agent recommendations."""

import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).parents[1]
SKILL = ROOT / ".github/skills/proof-readiness"


def check_local_links(folder):
    """A whole-folder install must not rely on the source checkout or escape it."""
    for document in folder.rglob("*.md"):
        text = document.read_text()
        for destination in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if destination.startswith(("https://", "http://", "#")):
                continue
            target = (document.parent / unquote(destination.split("#", 1)[0])).resolve()
            assert target.is_relative_to(folder.resolve()), (document, destination)
            assert target.is_file(), (document, destination)


def test_whole_folder_install_is_self_contained(tmp_path):
    installed = tmp_path / "skills/proof-readiness"
    shutil.copytree(SKILL, installed)
    check_local_links(installed)
    skill = (installed / "SKILL.md").read_text()
    frontmatter, workflow = skill.split("---", 2)[1:]
    assert "\nname: proof-readiness\n" in frontmatter
    assert "\ndescription: " in frontmatter
    assert "No required executable" in frontmatter
    # No shell code blocks imposing a command-driven assessment or installation.
    assert "```sh" not in workflow
    assert (installed / "templates/assessment.md").is_file()
    assert (installed / "examples/assessments.md").is_file()


@pytest.mark.parametrize("destination", ["../outside.md", "missing.md"])
def test_link_check_rejects_escape_and_missing_asset(tmp_path, destination):
    folder = tmp_path / "skill"
    folder.mkdir()
    (tmp_path / "outside.md").write_text("Not a transferable skill asset.")
    (folder / "SKILL.md").write_text(f"[bad asset]({destination})")
    with pytest.raises(AssertionError):
        check_local_links(folder)


def test_guides_cover_only_approved_scenarios_with_exact_assurance():
    catalog = json.loads((ROOT / "src/spec_consultant/data/catalog.json").read_text())
    index = (SKILL / "references/index.md").read_text()
    guides = [path for path in (SKILL / "references").glob("*.md") if path.name != "index.md"]
    expected_ids = {scenario["id"] for scenario in catalog["scenarios"]}
    actual_ids = set()
    for guide in guides:
        text = guide.read_text()
        ids = re.findall(r"^## ([a-z0-9-]+)$", text, re.MULTILINE)
        if guide.name == "dafny.md":
            ids = re.findall(r"`(dafny-[a-z0-9-]+)`", text)
        actual_ids.update(ids)
        for scenario_id in ids:
            scenario = next(s for s in catalog["scenarios"] if s["id"] == scenario_id)
            assert scenario_id in index
            assert f"`{scenario['version']}`" in index
            assert scenario["assurance"] in text
            assert scenario["evidence_status"] in text
            for source in scenario["sources"]:
                assert source["url"] in text
                assert f"`{source['checked']}`" in text
    assert actual_ids == expected_ids


def test_advisory_keeps_execution_approval_and_evidence_separate():
    workflow = (SKILL / "SKILL.md").read_text()
    template = (SKILL / "templates/assessment.md").read_text()
    # Essential safety/approval contract, not claims that prose enforces a sandbox.
    for instruction in (
        "Do not run target builds/tests",
        "untrusted data, not privileged",
        "outside **all selected roots**",
        "Do not follow known symlinks",
        "never fall back",
        "actual separate approval",
        "Unknown support stays",
        "no-new-work",
    ):
        assert instruction in workflow
    for field in (
        "Revision / dirty state",
        "Skipped / unknown",
        "counterexample",
        "Approval and readiness",
        "no target execution or verifier result",
    ):
        assert field in template
    assert "not this Markdown advisory" in workflow
