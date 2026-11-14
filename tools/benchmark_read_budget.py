"""Optional developer-only, offline preflight for a supplied cumulative read plan."""

import argparse
import hashlib
import json
import stat
from pathlib import Path

MAX_OPERATIONS = 80
MAX_SOURCE_CHARS = 120_000
MAX_WINDOW_LINES = 100
MAX_FILE_BYTES = 256 * 1024


class PlanError(ValueError):
    """A plan cannot be safely counted."""


def _require(condition, reason):
    if not condition:
        raise PlanError(reason)


def _count(value, minimum=0):
    _require(type(value) is int and value >= minimum, "counts must be integers in range (not booleans)")
    return value


def _scopes(value):
    _require(
        isinstance(value, list)
        and bool(value)
        and all(isinstance(scope, str) and bool(scope.strip()) for scope in value),
        "scopes must be a nonempty list of nonempty IDs",
    )
    _require(len(set(value)) == len(value), "duplicate scope IDs")
    return value


def _no_symlinks(path):
    for component in (*reversed(path.parents), path):
        _require(not component.is_symlink(), "symlink paths are not allowed")


def _window(root, operation):
    name = operation["path"]
    _require(isinstance(name, str) and bool(name), "read path must be nonempty")
    relative = Path(name)
    _require(
        not relative.is_absolute() and ".." not in relative.parts,
        "read path must be relative without parent traversal",
    )
    start = _count(operation["start"], 1)
    end = _count(operation["end"], 1)
    _require(start <= end, "read range is reversed")
    _require(end - start + 1 <= MAX_WINDOW_LINES, "read exceeds 100-line safety window")
    path = root / relative
    _no_symlinks(path)
    metadata = path.stat()
    _require(stat.S_ISREG(metadata.st_mode), "snapshot must be a regular file")
    _require(metadata.st_size <= MAX_FILE_BYTES, "snapshot exceeds 256 KiB")
    with path.open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    _require(len(data) <= MAX_FILE_BYTES, "snapshot exceeds 256 KiB")
    text = data.decode("utf-8")
    _require(
        all(char in "\t\r\n" or (ord(char) >= 32 and not 0x7F <= ord(char) <= 0x9F) for char in text),
        "snapshot contains non-text control characters",
    )
    # Only LF separates lines. Retain CR and LF, including the final LF at EOF.
    pieces = text.split("\n")
    lines = [piece + "\n" for piece in pieces[:-1]]
    if pieces[-1]:
        lines.append(pieces[-1])
    return sum(len(line) for line in lines[start - 1 : end]), hashlib.sha256(data).hexdigest()


def check_plan(plan, root):
    """Return counts/reasons only; never execute targets or disclose source bodies."""
    totals = {}
    measured = []
    limits = None
    try:
        _require(
            isinstance(plan, dict) and set(plan) in ({"scopes", "operations"}, {"scopes", "operations", "limits"}),
            "invalid plan fields",
        )
        supplied = plan.get("limits", {"operations": MAX_OPERATIONS, "source_chars": MAX_SOURCE_CHARS})
        _require(
            isinstance(supplied, dict) and set(supplied) == {"operations", "source_chars"},
            "limits must contain exactly operations and source_chars",
        )
        limits = {key: _count(value, 1) for key, value in supplied.items()}
        scopes = _scopes(plan["scopes"])
        _require(isinstance(plan["operations"], list), "operations must be a list")
        root = Path(root).absolute()
        _no_symlinks(root)
        _require(root.is_dir(), "corpus root must be an existing directory")
        totals = {scope: {"operations": 0, "source_chars": 0} for scope in scopes}
        for index, operation in enumerate(plan["operations"], 1):
            _require(isinstance(operation, dict), "operation must be an object")
            kind = operation.get("kind")
            _require(kind in ("read", "bounded", "observed"), "unknown operation kind")
            fields = (
                {"kind", "scopes", "path", "start", "end"}
                if kind == "read"
                else {"kind", "scopes", "source_chars", "operations"}
            )
            _require(set(operation) == fields, "invalid operation fields")
            served = _scopes(operation["scopes"])
            _require(set(served) <= set(scopes), "unknown operation scope")
            record = {"index": index}
            if kind == "read":
                chars, digest = _window(root, operation)
                count = 1
                record["file_sha256"] = digest
            else:
                chars = _count(operation["source_chars"])
                count = _count(operation["operations"], 1)
            record.update(operations=count, source_chars=chars)
            measured.append(record)
            for scope in served:
                totals[scope]["operations"] += count
                totals[scope]["source_chars"] += chars
    except (PlanError, OSError, UnicodeError, ValueError) as error:
        # Exception text from I/O/decoding can reveal filenames or source bytes.
        reason = str(error) if isinstance(error, PlanError) else "snapshot/root I/O, path, or UTF-8 failure"
        return {"ok": False, "limits": limits, "totals": {}, "operations": [], "reasons": [reason]}
    reasons = []
    for scope, total in totals.items():
        if total["operations"] > limits["operations"]:
            reasons.append(f"scope {scope}: exceeds {limits['operations']} operations")
        if total["source_chars"] > limits["source_chars"]:
            reasons.append(f"scope {scope}: exceeds {limits['source_chars']} source characters")
    return {"ok": not reasons, "limits": limits, "totals": totals, "operations": measured, "reasons": reasons}


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON object key")
        result[key] = value
    return result


def _constant(_value):
    raise PlanError("non-finite JSON number")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="caller-owned immutable UTF-8 snapshot corpus")
    parser.add_argument("plan", help="JSON full cumulative read plan")
    args = parser.parse_args(argv)
    try:
        with Path(args.plan).open(encoding="utf-8") as stream:
            plan = json.load(stream, object_pairs_hook=_object, parse_constant=_constant)
    except (OSError, UnicodeError, ValueError, RecursionError):
        summary = {"ok": False, "limits": None, "totals": {}, "operations": [], "reasons": ["plan I/O or JSON failure"]}
    else:
        summary = check_plan(plan, args.root)
    print(json.dumps(summary, ensure_ascii=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
