"""Bounded read-only profiling. Target content is never executed or imported."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import tomllib
from collections import Counter
from pathlib import Path, PurePosixPath

from .source import inspect_source

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "vendor",
    "target",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".terraform",
    ".config",
    ".aws",
    ".ssh",
    ".gnupg",
    "secrets",
    ".secrets",
}
LANGUAGES = {
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".java": "java",
    ".dfy": "dafny",
    ".tla": "tla",
    ".v": "coq",
    ".lean": "lean",
    ".smt2": "smtlib",
    ".bpl": "boogie",
    ".pml": "promela",
    ".als": "alloy",
}
MANIFESTS = {"Cargo.toml", "pyproject.toml", "package.json", "go.mod", "Cargo.lock"}
BUILD = {
    "CMakeLists.txt",
    "Makefile",
    "meson.build",
    "build.rs",
    "rust-toolchain.toml",
    ".gitmodules",
    "azure-pipelines.yml",
    "Jenkinsfile",
    ".travis.yml",
}
PATTERNS = {
    "function": r"\b(?:fn|def|function|method)\s+\w+|\b\w+\s+\w+\s*\([^;]*\)\s*\{",
    "arithmetic": r"\b(?:checked_add|checked_sub|wrapping_add|saturating_add)\b|[+*%]|(?<!-)-(?!>)",
    "indexing": r"\b(?:slice|Vec|vector|memcpy|memmove|buffer)\b|\w+\s*\[[^]]+\]",
    "unsafe": r"\bunsafe\b|\*\s*(?:mut|const)\b",
    "ffi": r'\bextern\s+"|\bextern\s*\(|\b(?:bindgen|cxx|ctypes)\b',
    "linkage": r'\bextern\s+"',
    "concurrency": r"\b(?:thread|spawn|Mutex|RwLock|Atomic\w*|pthread_\w*|mutex)\b",
    "async": r"\b(?:async|await)\b",
    "assembly": r"\b(?:asm|global_asm|__asm__)\s*[!(]",
    "dynamic_dispatch": r"\bdyn\s+\w+|\bvirtual\b",
    "state_machine": r"\b(?:enum|transition|state|State|Next|VARIABLES)\b",
    "bitwise": r"<<|>>|(?<!&)&(?!&)|(?<!\|)\|(?!\|)|\^",
    "contracts": r"\b(?:requires|ensures|invariant|__CPROVER_assert)\b",
    "kani": r"#\s*\[\s*kani::proof",
    "verus": r"\bverus!\s*\{",
    "tests": r"#\s*\[\s*test\s*]|\b(?:assert|assert_eq|test_\w+)\b",
}
SYMBOL = re.compile(r"\b(?:fn|def|function|method)\s+([A-Za-z_]\w*)")
C_SYMBOL = re.compile(r"\b(?:[A-Za-z_][\w:<>]*[ \t*&]+)+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{")


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value:
        raise ValueError(f"unsafe relative path: {value!r}")
    if value != path.as_posix() or value == ".":
        raise ValueError(f"noncanonical relative path: {value!r}")
    return path


def is_secret(path: str) -> bool:
    parts = PurePosixPath(path).parts
    for part in parts:
        name = part.lower()
        if (
            name
            in {
                ".env",
                ".netrc",
                ".npmrc",
                ".pypirc",
                ".git-credentials",
                "credentials",
                "id_rsa",
                "id_ed25519",
                "id_dsa",
                "id_ecdsa",
            }
            or name.startswith(".env.")
            or any(word in name for word in ("secret", "credential", "private_key"))
            or name.endswith((".pem", ".key", ".p12", ".pfx", ".keystore"))
        ):
            return True
    return False


def open_directory(root: Path, parts: tuple[str, ...]) -> int:
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        return directory
    except BaseException:
        os.close(directory)
        raise


def read_safe(root: Path, relative: str, limit: int) -> bytes:
    """Use directory descriptors so ancestor symlink swaps cannot escape the root."""
    parts = safe_relative(relative).parts
    if is_secret(relative) or any(part in SKIP_DIRS for part in parts):
        raise ValueError("excluded path")
    directory = open_directory(root, parts[:-1])
    try:
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("not a regular file")
            with os.fdopen(fd, "rb", closefd=False) as stream:
                data = stream.read(limit + 1)
            if len(data) > limit:
                raise ValueError("file exceeds byte limit")
            return data
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def git_identity(root: Path) -> dict:
    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            env={
                **{key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
            },
            check=True,
        )
        return result.stdout.strip()

    try:
        top = run("rev-parse", "--show-toplevel")
        status = run("status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=all")
        try:
            revision = run("rev-parse", "--verify", "HEAD")
        except subprocess.CalledProcessError:
            revision = None
        return {
            "available": True,
            "top_level": top,
            "revision": revision,
            "dirty": bool(status),
            "status_scope": "Git worktree; submodule contents uninspected",
        }
    except (OSError, subprocess.SubprocessError):
        return {
            "available": False,
            "top_level": None,
            "revision": None,
            "dirty": None,
            "status_scope": "unknown",
        }


def file_kind(relative: str) -> str:
    path = PurePosixPath(relative)
    if path.name in MANIFESTS:
        return "manifest"
    if path.name in BUILD or relative.startswith((".github/workflows/", ".gitlab-ci", ".circleci/")):
        return "configuration"
    if path.suffix in {".tla", ".dfy", ".v", ".lean", ".smt2", ".bpl", ".pml", ".als", ".spec"}:
        return "specification"
    if path.suffix == ".cfg":
        return "configuration"
    if any(part in {"benches", "benchmarks", "benchmark"} for part in path.parts):
        return "benchmark"
    if any(part in {"examples", "fuzz"} for part in path.parts):
        return "example"
    if "test" in path.name.lower() or "tests" in path.parts:
        return "test"
    return "source" if path.suffix in LANGUAGES else "other"


def dependencies(relative: str, text: str) -> list[dict]:
    result = []
    if PurePosixPath(relative).name == "Cargo.toml":
        try:
            manifest = tomllib.loads(text)
            sections = {key: value for key, value in manifest.items() if "dependencies" in key}
            sections.update(
                {
                    f"workspace.{key}": value
                    for key, value in manifest.get("workspace", {}).items()
                    if "dependencies" in key
                }
            )
            for platform, tables in manifest.get("target", {}).items():
                for key, value in tables.items():
                    if "dependencies" in key:
                        sections[f"target.{platform}.{key}"] = value
            for section, table in sections.items():
                if not isinstance(table, dict):
                    continue
                for name, value in table.items():
                    if re.fullmatch(r"[A-Za-z0-9_-]+", name):
                        target = value.get("path") if isinstance(value, dict) else None
                        if not isinstance(target, str):
                            target = None
                        result.append(
                            {
                                "manifest": relative,
                                "name": name,
                                "relationship": section,
                                "target": target,
                            }
                        )
        except (ValueError, TypeError, AttributeError):
            pass
    if PurePosixPath(relative).name == "CMakeLists.txt":
        for match in re.finditer(r"\b(add_subdirectory|target_link_libraries)\s*\(([^)\n]+)", text):
            tokens = re.findall(r"[A-Za-z0-9_./+-]+", match[2])
            if tokens:
                result.append(
                    {
                        "manifest": relative,
                        "name": tokens[0],
                        "relationship": match[1],
                        "target": " ".join(tokens[1:]) or None,
                    }
                )
    return result


def profile_root(root: Path, root_id: str, *, max_files: int, max_bytes: int, max_entries: int, max_depth: int) -> dict:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    files, omitted, deps = [], [], []
    counts: Counter = Counter()
    visited = 0
    stop = False

    def skip(path: str, reason: str) -> None:
        # Secret filenames and contents are not serialized.
        omitted.append({"path": "[redacted]" if is_secret(path) else path, "reason": reason})

    def walk(directory: Path, depth: int) -> None:
        nonlocal visited, stop
        try:
            directory_fd = open_directory(root, directory.relative_to(root).parts)
            try:
                with os.scandir(directory_fd) as stream:
                    entries = []
                    for entry in stream:
                        visited += 1
                        if visited > max_entries:
                            skip(
                                directory.relative_to(root).as_posix(),
                                "entry limit; directory and remaining paths uninspected",
                            )
                            stop = True
                            return
                        # Cache type information while the directory descriptor is open.
                        entries.append((entry.name, entry.is_symlink(), entry.is_dir(follow_symlinks=False)))
            finally:
                os.close(directory_fd)
            if depth and any(name == ".git" for name, _, _ in entries):
                skip(directory.relative_to(root).as_posix(), "nested repository/submodule; select as an explicit root")
                return
            for name, symlink, is_directory in sorted(entries):
                if len(files) >= max_files:
                    skip(".", "file limit; remaining paths uninspected")
                    stop = True
                    break
                relative = (directory / name).relative_to(root).as_posix()
                if is_secret(relative):
                    skip(relative, "secret-like path")
                    continue
                if symlink:
                    skip(relative, "symlink; never followed")
                    continue
                if is_directory:
                    if name in SKIP_DIRS:
                        skip(relative, "dependency/build/private directory")
                    elif depth >= max_depth:
                        skip(relative, "depth limit")
                    else:
                        walk(directory / name, depth + 1)
                    if stop:
                        break
                    continue
                try:
                    data = read_safe(root, relative, max_bytes)
                    if b"\x00" in data:
                        skip(relative, "binary content")
                        continue
                    text = data.decode("utf-8")
                except (OSError, ValueError, UnicodeError) as exc:
                    skip(relative, f"unreadable, excluded, or oversized ({type(exc).__name__})")
                    continue
                language = LANGUAGES.get(Path(relative).suffix, "unknown")
                signals, symbols = inspect_source(text, language, PATTERNS)
                files.append(
                    {
                        "path": relative,
                        "language": language,
                        "kind": file_kind(relative),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "lines": len(text.splitlines()),
                        "signals": signals,
                        "symbols": symbols,
                    }
                )
                deps.extend(dependencies(relative, text))
                counts[language] += 1
        except OSError:
            skip(directory.relative_to(root).as_posix(), "directory unreadable")

    before = git_identity(root)
    walk(root, 0)
    after = git_identity(root)
    return {
        "id": root_id,
        "path": str(root),
        "git": after,
        "changed_during_scan": before != after,
        "files": files,
        "languages": dict(sorted(counts.items())),
        "dependencies": deps,
        "uninspected": omitted,
        "limits": {
            "max_files": max_files,
            "max_bytes": max_bytes,
            "max_entries": max_entries,
            "max_depth": max_depth,
        },
        "coverage": "bounded discovery; not comprehensive",
        "snapshot": hashlib.sha256("\n".join(f"{f['path']}:{f['sha256']}" for f in files).encode()).hexdigest(),
    }


def profile(
    roots: list[str],
    *,
    max_files: int = 250,
    max_bytes: int = 262144,
    max_entries: int = 5000,
    max_depth: int = 20,
) -> dict:
    if not roots or min(max_files, max_bytes, max_entries, max_depth) < 1:
        raise ValueError("provide roots and positive scan limits")
    resolved = [Path(root).expanduser().resolve(strict=True) for root in roots]
    if len(set(resolved)) != len(resolved):
        raise ValueError("duplicate repository roots")
    return {
        "version": "2",
        "roots": [
            profile_root(
                root,
                f"r{i}",
                max_files=max_files,
                max_bytes=max_bytes,
                max_entries=max_entries,
                max_depth=max_depth,
            )
            for i, root in enumerate(resolved, 1)
        ],
    }
