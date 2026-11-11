"""Offline CLI. Only Git metadata commands are run against selected repositories."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from .matcher import ADOPTION, GOALS, assess, assessment_context, match_scenarios
from .profiler import profile
from .render import artifacts
from .runtime import check_declared_roots, runtime_info
from .validation import (
    catalog,
    freshness,
    resource,
    validate_assessment,
    validate_catalog,
    validate_profile,
)


def load(path: str) -> dict:
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def dump(value: dict) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True) + "\n"


def outside_roots(path: Path, profiled: dict) -> Path:
    resolved = path.expanduser().resolve()
    for root in profiled["roots"]:
        selected = Path(root["path"]).resolve()
        if resolved == selected or selected in resolved.parents:
            raise ValueError(f"output must be outside assessed roots: {resolved}")
    return resolved


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="spec-consultant",
        description="Offline, provisional specification opportunity assessment",
    )
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("runtime-info", help="Machine-readable interpreter, build, data and notices identity")
    for name in ("profile", "assess"):
        command = commands.add_parser(name)
        command.add_argument("roots", nargs="+" if name == "profile" else "*")
        command.add_argument("--max-files", type=int, default=250)
        command.add_argument("--max-bytes", type=int, default=262144)
        command.add_argument("--max-entries", type=int, default=5000)
        command.add_argument("--max-depth", type=int, default=20)
        if name == "profile":
            command.add_argument("-o", "--output", required=True)
        else:
            command.add_argument("--profile", dest="profile_file")
            command.add_argument("--max-candidates", type=int, default=3)
            command.add_argument("--goal", action="append", choices=GOALS, default=[])
            command.add_argument("--adoption", choices=ADOPTION, default="unknown")
            command.add_argument("--out", required=True)
    command = commands.add_parser("catalog", help="Retrieve local, pre-researched scenario entries")
    command.add_argument("--profile", dest="profile_file")
    command.add_argument("--scenario")
    command.add_argument("--goal", action="append", choices=GOALS, default=[])
    command.add_argument("--adoption", choices=ADOPTION, default="unknown")
    command = commands.add_parser("schema")
    command.add_argument("kind", choices=("assessment", "catalog"))
    command = commands.add_parser("validate-catalog", help="Validate a proposed catalog contribution")
    command.add_argument("catalog")
    command = commands.add_parser("validate")
    command.add_argument("assessment")
    command.add_argument(
        "--no-source-check",
        action="store_true",
        help="Archive/schema check only; does not establish current source integrity",
    )
    command = commands.add_parser("render")
    command.add_argument("assessment")
    command.add_argument("--out", required=True)
    command = commands.add_parser("freshness")
    command.add_argument("assessment")
    return result


def run(args: argparse.Namespace) -> int:
    check_declared_roots(args)
    if args.command == "runtime-info":
        print(dump(runtime_info()), end="")
        return 0
    if args.command in {"profile", "assess"}:
        if args.command == "assess" and args.profile_file:
            if args.roots:
                raise ValueError("use roots or --profile, not both")
            profiled = load(args.profile_file)
            validate_profile(profiled)
            if freshness({"profile": profiled}):
                raise ValueError("saved profile is stale; profile the selected roots again")
        else:
            profiled = profile(
                args.roots,
                max_files=args.max_files,
                max_bytes=args.max_bytes,
                max_entries=args.max_entries,
                max_depth=args.max_depth,
            )
        if args.command == "profile":
            validate_profile(profiled)
            output = outside_roots(Path(args.output), profiled)
            write(output, dump(profiled))
            print(f"Profile: {output} (bounded discovery; not comprehensive)")
        else:
            assessment = assess(profiled, max_candidates=args.max_candidates, goals=args.goal, adoption=args.adoption)
            validate_assessment(assessment)
            output = outside_roots(Path(args.out), profiled)
            canonical = outside_roots(output / "assessment.json", profiled)
            rendered = artifacts(assessment, str(canonical))
            paths = {name: outside_roots(output / name, profiled) for name in rendered}
            write(canonical, dump(assessment))
            for name, text in rendered.items():
                write(paths[name], text)
            print(f"Provisional assessment and three rendered artifacts: {output}")
        return 0
    if args.command == "catalog":
        knowledge = catalog()
        if args.profile_file:
            profiled = load(args.profile_file)
            validate_profile(profiled)
            matches = match_scenarios(profiled, knowledge, assessment_context(args.goal, args.adoption))
            relevant = {match["scenario"] for match in matches if match["status"] != "excluded"}
            knowledge = {
                **knowledge,
                "scenarios": [entry for entry in knowledge["scenarios"] if entry["id"] in relevant],
            }
        if args.scenario:
            knowledge = {
                **knowledge,
                "scenarios": [entry for entry in knowledge["scenarios"] if entry["id"] == args.scenario],
            }
            if not knowledge["scenarios"]:
                raise ValueError("scenario not found in selected catalog coverage")
        print(dump(knowledge), end="")
        return 0
    if args.command == "schema":
        print(dump(resource(f"{args.kind}.schema.json")), end="")
        return 0
    if args.command == "validate-catalog":
        validate_catalog(load(args.catalog))
        print("Valid documented catalog structure and template graphs; primary-source review still required.")
        return 0
    value = load(args.assessment)
    validate_assessment(
        value,
        check_sources=args.command != "freshness" and not getattr(args, "no_source_check", False),
    )
    if args.command == "validate":
        print(
            "Valid structure, graph, and catalog claims; "
            + ("source checks SKIPPED. " if args.no_source_check else "referenced hashes checked. ")
            + "Recommendation correctness is not established."
        )
    elif args.command == "freshness":
        changes = freshness(value)
        if changes:
            print("\n".join(changes))
            return 1
        print("Observed snapshot, Git identity/status, and scan coverage unchanged; not an atomic scan.")
    elif args.command == "render":
        output = outside_roots(Path(args.out), value["profile"])
        rendered = artifacts(value, str(Path(args.assessment).resolve()))
        paths = {name: outside_roots(output / name, value["profile"]) for name in rendered}
        for name, text in rendered.items():
            write(paths[name], text)
        print(f"Rendered canonical assessment: {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parser().parse_args(argv))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"spec-consultant: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
