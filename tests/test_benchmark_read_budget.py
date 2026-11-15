"""Synthetic fixtures only: offline supplied-plan counting, not campaign evaluation."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "tools" / "benchmark_read_budget.py"
SPEC = importlib.util.spec_from_file_location("benchmark_read_budget", SCRIPT)
budget = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(budget)


def cost(chars, operations=1, kind="bounded", scopes=None):
    return {
        "kind": kind,
        "scopes": ["selector"] if scopes is None else scopes,
        "source_chars": chars,
        "operations": operations,
    }


def plan(*operations, scopes=None):
    return {"scopes": ["selector"] if scopes is None else scopes, "operations": list(operations)}


def read(path="snapshot.txt", start=1, end=1, scopes=None):
    return {
        "kind": "read",
        "scopes": ["selector"] if scopes is None else scopes,
        "path": path,
        "start": start,
        "end": end,
    }


def test_failed_campaign_costs_rejected_before_actions(tmp_path):
    selector = budget.check_plan(plan(cost(93300, 40), cost(47033, 25)), tmp_path)
    assert not selector["ok"]
    assert selector["totals"]["selector"] == {"operations": 65, "source_chars": 140333}
    reviewer = budget.check_plan(plan(cost(164869, 34)), tmp_path)
    assert not reviewer["ok"]
    assert reviewer["totals"]["selector"] == {"operations": 34, "source_chars": 164869}
    assert reviewer["limits"] == selector["limits"] == {"operations": 80, "source_chars": 120000}


def test_explicit_future_frozen_limits_and_shared_costs(tmp_path):
    future = plan(
        cost(93300, 40, scopes=["selector", "reviewer"]),
        cost(47033, 25, scopes=["selector", "reviewer"]),
        cost(10000, 5, "observed", scopes=["selector", "reviewer"]),
        scopes=["selector", "reviewer"],
    )
    future["limits"] = {"operations": 80, "source_chars": 250000}
    result = budget.check_plan(future, tmp_path)
    assert result["ok"] and result["limits"] == future["limits"]
    assert result["totals"] == {scope: {"operations": 70, "source_chars": 150333} for scope in ["selector", "reviewer"]}
    future["limits"]["operations"] = 69
    assert not budget.check_plan(future, tmp_path)["ok"]
    future["limits"]["operations"] = 100
    future["operations"] = [cost(164869, 34)]
    assert budget.check_plan(future, tmp_path)["ok"]
    future["operations"] = [read(end=101)]
    assert not budget.check_plan(future, tmp_path)["ok"]
    future["operations"] = [read()]
    (tmp_path / "snapshot.txt").write_bytes(b"x" * (256 * 1024 + 1))
    assert budget.check_plan(future, tmp_path)["reasons"] == ["snapshot exceeds 256 KiB"]


@pytest.mark.parametrize(
    "limits",
    [
        None,
        {},
        {"source_chars": 250000},
        {"source_chars": 250000, "operations": 80, "extra": 1},
        *[{"source_chars": value, "operations": 80} for value in (True, 0, -1, 1.5, "250000")],
        *[{"source_chars": 250000, "operations": value} for value in (False, 0, -1, 1.5)],
    ],
)
def test_invalid_limits_fail_closed(tmp_path, limits):
    supplied = plan(cost(1))
    supplied["limits"] = limits
    result = budget.check_plan(supplied, tmp_path)
    assert not result["ok"] and result["limits"] is None and result["totals"] == {}


def test_lf_unicode_crlf_eof_and_shared_charges(tmp_path):
    data = "é\r\nα\u2028SECRET\u2029tail\r\nlast"
    (tmp_path / "snapshot.txt").write_bytes(data.encode("utf-8"))
    shared = read(start=2, end=3, scopes=["selector", "reviewer"])
    result = budget.check_plan(plan(shared, scopes=["selector", "reviewer"]), tmp_path)
    assert result["ok"]
    expected = len("α\u2028SECRET\u2029tail\r\nlast")
    assert result["totals"] == {
        scope: {"operations": 1, "source_chars": expected} for scope in ["selector", "reviewer"]
    }
    assert result["operations"][0]["file_sha256"] == hashlib.sha256(data.encode("utf-8")).hexdigest()
    assert "SECRET" not in json.dumps(result)
    assert budget.check_plan(plan(read(end=100)), tmp_path)["totals"]["selector"]["source_chars"] == len(data)
    assert budget.check_plan(plan(read(start=99, end=100)), tmp_path)["totals"]["selector"]["source_chars"] == 0
    for end in (101, 200, 201):
        assert not budget.check_plan(plan(read(end=end)), tmp_path)["ok"]


def test_cumulative_costs_and_exact_caps(tmp_path):
    assert budget.check_plan(plan(cost(120000, 80, "observed")), tmp_path)["ok"]
    assert not budget.check_plan(plan(cost(120000, 79, "observed"), cost(1)), tmp_path)["ok"]
    assert not budget.check_plan(plan(cost(0, 80, "observed"), cost(0)), tmp_path)["ok"]


@pytest.mark.parametrize(
    "operation",
    [
        cost(-1),
        cost(True),
        cost(1.0),
        cost(1, 0),
        cost(1, -1),
        cost(1, False),
        cost(1, kind="fetch"),
        cost(1, scopes=[]),
        cost(1, scopes=[""]),
        cost(1, scopes=[" "]),
        cost(1, scopes=["other"]),
        cost(1, scopes=["selector", "selector"]),
        {"kind": "bounded", "source_chars": 1, "operations": 1},
        read(start=0),
        read(start=True),
        read(start=2, end=1),
        read(end=1.5),
    ],
)
def test_malformed_operations_fail_closed(tmp_path, operation):
    result = budget.check_plan(plan(operation), tmp_path)
    assert not result["ok"] and result["totals"] == {}


@pytest.mark.parametrize("scopes", [[], [""], ["selector", "selector"], "selector"])
def test_invalid_declared_scopes(tmp_path, scopes):
    assert not budget.check_plan(plan(cost(0), scopes=scopes), tmp_path)["ok"]


@pytest.mark.parametrize(
    ("character", "allowed"),
    [
        ("\x00", False),
        ("\x1f", False),
        ("\x7f", False),
        ("\x80", False),
        ("\x9b", False),
        ("\x9f", False),
        ("\x7e", True),
        ("\xa0", True),
        ("\u2028", True),
        ("\u2029", True),
        ("\t", True),
        ("\r\n", True),
    ],
)
def test_control_character_hygiene(tmp_path, character, allowed):
    body = f"A{character}31mB\n"
    (tmp_path / "owned.txt").write_bytes(body.encode("utf-8"))
    result = budget.check_plan(plan(read(path="owned.txt", end=2)), tmp_path)
    assert result["ok"] is allowed
    if allowed:
        assert result["totals"]["selector"]["source_chars"] == len(body)
    else:
        assert result["reasons"] == ["snapshot contains non-text control characters"]
        assert result["totals"] == {} and body not in json.dumps(result)


def test_unsafe_nontext_and_io_failures_without_bodies(tmp_path, monkeypatch):
    secret = b"PRIVATE_BODY"
    (tmp_path / "snapshot.txt").write_bytes(secret)
    (tmp_path / "link").symlink_to(tmp_path / "snapshot.txt")
    (tmp_path / "directory").mkdir()
    (tmp_path / "linked_directory").symlink_to(tmp_path / "directory", target_is_directory=True)
    for name in (
        str(tmp_path / "snapshot.txt"),
        "../snapshot.txt",
        "link",
        "linked_directory/snapshot.txt",
        "directory",
        "missing",
    ):
        result = budget.check_plan(plan(read(path=name)), tmp_path)
        assert not result["ok"]
        assert "PRIVATE_BODY" not in json.dumps(result) and str(tmp_path) not in json.dumps(result)
    for data in (b"\xffPRIVATE_BODY", b"\x00PRIVATE_BODY", b"x" * (256 * 1024 + 1)):
        (tmp_path / "snapshot.txt").write_bytes(data)
        assert not budget.check_plan(plan(read()), tmp_path)["ok"]
    (tmp_path / "snapshot.txt").write_bytes(secret)
    (tmp_path / "root_link").symlink_to(tmp_path, target_is_directory=True)
    assert not budget.check_plan(plan(read()), tmp_path / "root_link")["ok"]
    original = Path.open

    def denied(path, *args, **kwargs):
        if path.name == "snapshot.txt":
            raise PermissionError(f"PRIVATE_BODY {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", denied)
    result = budget.check_plan(plan(read()), tmp_path)
    assert not result["ok"] and "PRIVATE_BODY" not in json.dumps(result)


def test_cli_json_results_and_parse_errors(tmp_path, capsys):
    filename = tmp_path / "plan.json"
    filename.write_text(json.dumps(plan(cost(42))), encoding="utf-8")
    assert budget.main(["--root", str(tmp_path), str(filename)]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["selector"]["source_chars"] == 42
    filename.write_text(json.dumps(plan(cost(140333, 65))), encoding="utf-8")
    assert budget.main(["--root", str(tmp_path), str(filename)]) == 1
    assert not json.loads(capsys.readouterr().out)["ok"]
    for malformed in ('{"PRIVATE_BODY":', '{"scopes":[],"scopes":[],"operations":[]}', "NaN"):
        filename.write_text(malformed, encoding="utf-8")
        assert budget.main(["--root", str(tmp_path), str(filename)]) == 1
        output = capsys.readouterr().out
        assert not json.loads(output)["ok"] and "PRIVATE_BODY" not in output
    filename.write_bytes(b"\xffPRIVATE_BODY")
    assert budget.main(["--root", str(tmp_path), str(filename)]) == 1
    assert "PRIVATE_BODY" not in capsys.readouterr().out
    filename.write_text(json.dumps(plan(read())), encoding="utf-8")
    for data in (b"\xffPRIVATE_BODY", b"\x00PRIVATE_BODY"):
        (tmp_path / "snapshot.txt").write_bytes(data)
        assert budget.main(["--root", str(tmp_path), str(filename)]) == 1
        output = capsys.readouterr().out
        assert not json.loads(output)["ok"]
        assert "PRIVATE_BODY" not in output and str(tmp_path) not in output
