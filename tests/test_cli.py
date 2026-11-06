import json
from pathlib import Path

from spec_consultant.cli import main
from spec_consultant.render import artifacts

from .conftest import EXAMPLE


def test_end_to_end_and_canonical_render(tmp_path, capsys):
    output = tmp_path / "output"
    assert main(["assess", str(EXAMPLE), "--out", str(output)]) == 0
    canonical = output / "assessment.json"
    assessment = json.loads(canonical.read_text())
    assert set(path.name for path in output.iterdir()) == {
        "assessment.json",
        "report.md",
        "backlog.md",
        "orchestrator.md",
    }
    assert main(["validate", str(canonical)]) == 0
    assert main(["freshness", str(canonical)]) == 0
    rerendered = tmp_path / "rendered"
    assert main(["render", str(canonical), "--out", str(rerendered)]) == 0
    for name in artifacts(assessment, str(canonical)):
        assert (output / name).read_bytes() == (rerendered / name).read_bytes()
    report = (output / "report.md").read_text()
    assert "static-provisional" in report
    assert "not-run" in report
    assert "https://model-checking.github.io/kani/" in report
    prompt = (output / "orchestrator.md").read_text()
    for required in (
        "Inferred requirements are NOT",
        "Never weaken specifications",
        "full output",
        "dirty",
        str(EXAMPLE),
        "w1-inspect",
        "untrusted",
        "Project approval policy",
        "dependency",
    ):
        assert required in prompt
    assert "Recommendation correctness" in capsys.readouterr().out


def test_profile_catalog_and_schema(tmp_path, capsys):
    path = tmp_path / "profile.json"
    assert main(["profile", str(EXAMPLE), "-o", str(path)]) == 0
    capsys.readouterr()
    assert main(["catalog", "--profile", str(path), "--scenario", "kani-rust-slices"]) == 0
    knowledge = json.loads(capsys.readouterr().out)
    assert len(knowledge["scenarios"]) == 1
    assert main(["schema", "assessment"]) == 0
    assert "$schema" in json.loads(capsys.readouterr().out)
    output = tmp_path / "assessment"
    assert main(["assess", "--profile", str(path), "--out", str(output)]) == 0


def test_reject_writing_inside_any_target(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "lib.rs").write_text("fn f(x: u8) -> u8 { x + 1 }\n")
    assert main(["assess", str(root), "--out", str(root / "output")]) == 2
    assert not (root / "output").exists()
    assert main(["profile", str(root), "-o", str(root / "profile.json")]) == 2
    link = tmp_path / "alias"
    link.symlink_to(root, target_is_directory=True)
    assert main(["assess", str(root), "--out", str(link / "output")]) == 2


def test_cli_errors_and_archive_mode(tmp_path, capsys):
    path = tmp_path / "broken.json"
    path.write_text("{}")
    assert main(["validate", str(path)]) == 2
    assert "schema" in capsys.readouterr().err
    assert main(["assess", "--out", str(tmp_path / "out")]) == 2
    assert main(["catalog", "--scenario", "nonexistent"]) == 2
    assert main(["assess", str(EXAMPLE), "--out", str(tmp_path / "out")]) == 0
    canonical = tmp_path / "out" / "assessment.json"
    assert main(["validate", str(canonical), "--no-source-check"]) == 0
    assert "SKIPPED" in capsys.readouterr().out


def test_skill_format():
    skill = Path(__file__).parents[1] / ".github/skills/proof-readiness/SKILL.md"
    text = skill.read_text()
    frontmatter = text.split("---", 2)[1]
    assert "\nname: proof-readiness\n" in frontmatter
    assert "\ndescription: " in frontmatter
    assert "spec-consultant freshness" in text


def test_assessment_filters_and_stale_saved_profile(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "lib.rs"
    source.write_text("fn sum(buffer: &[u8]) -> u8 { buffer[0] + 1 }\n")
    path = tmp_path / "profile.json"
    output = tmp_path / "out"
    assert main(["profile", str(root), "-o", str(path)]) == 0
    assert (
        main(
            [
                "assess",
                "--profile",
                str(path),
                "--goal",
                "memory-safety",
                "--adoption",
                "no-production-changes",
                "--out",
                str(output),
            ]
        )
        == 0
    )
    value = json.loads((output / "assessment.json").read_text())
    assert len(value["work_items"]) == 2
    source.write_text("fn sum(buffer: &[u8]) -> u8 { buffer[0] + 2 }\n")
    assert main(["assess", "--profile", str(path), "--out", str(output)]) == 2
    assert main(["freshness", str(output / "assessment.json")]) == 1


def test_catalog_contribution_command(tmp_path):
    from spec_consultant.validation import catalog

    proposed = tmp_path / "catalog.json"
    proposed.write_text(json.dumps(catalog()))
    assert main(["validate-catalog", str(proposed)]) == 0


def test_assessment_does_not_execute_target_code(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    marker = tmp_path / "must-not-exist"
    (root / "setup.py").write_text(f"open({str(marker)!r}, 'w').write('executed')\n")
    (root / "build.rs").write_text('compile_error!("target execution forbidden");\n')
    (root / "Makefile").write_text(f"all:\n\ttouch {marker}\n")
    assert main(["assess", str(root), "--out", str(tmp_path / "out")]) == 0
    assert not marker.exists()
