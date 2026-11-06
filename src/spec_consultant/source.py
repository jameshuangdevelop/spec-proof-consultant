"""Small lexical filter, not a parser, preprocessor, or call-graph analysis."""

from __future__ import annotations

import re

RUST_RAW = re.compile(r'(?:br|r)(#*)"')
CPP_RAW = re.compile(r'R"([^ ()\\\t\r\n]{0,16})\(')
CHAR = re.compile(r"'(?:\\(?:x[0-9a-fA-F]{2}|u\{[0-9a-fA-F]+\}|.)|[^'\\\n])'")


def code_view(text: str, language: str) -> str:
    """Mask comments/literals without moving offsets; preserve actual linkage literals."""
    if language not in {"rust", "c", "cpp"}:
        return text
    result = list(text)
    i = 0

    def mask(start: int, end: int) -> None:
        for offset in range(start, end):
            if result[offset] != "\n":
                result[offset] = " "

    while i < len(text):
        start = i
        if text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
        elif text.startswith("/*", i):
            i += 2
            depth = 1
            while i < len(text) and depth:
                if language == "rust" and text.startswith("/*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
        else:
            raw = RUST_RAW.match(text, i) if language == "rust" and text[i] in {"b", "r"} else None
            cpp_raw = CPP_RAW.match(text, i) if language == "cpp" and text[i] == "R" else None
            if raw or cpp_raw:
                match = raw or cpp_raw
                closing = '"' + match[1] if raw else ")" + match[1] + '"'
                end = text.find(closing, match.end())
                i = len(text) if end < 0 else end + len(closing)
            elif text[i] == '"':
                i += 1
                while i < len(text):
                    if text[i] == "\\":
                        i += 2
                    elif text[i] == '"':
                        i += 1
                        break
                    else:
                        i += 1
                if re.search(r"\bextern\s*$", "".join(result[max(0, start - 100) : start])):
                    # "C" denotes linkage, unlike an arbitrary prose/code example literal.
                    continue
            elif text[i] == "'":
                char = CHAR.match(text, i)
                if not char:
                    i += 1  # Rust lifetime, not a character literal.
                    continue
                i = char.end()
            else:
                i += 1
                continue
        mask(start, min(i, len(text)))
    return "".join(result)


def definitions(code: str, language: str) -> list[dict]:
    if language == "rust":
        pattern = r"\bfn\s+([A-Za-z_]\w*)[^;{}]*\{"
    elif language in {"c", "cpp"}:
        pattern = (
            r"(?m)^[ \t]*(?:[A-Za-z_][\w:<>]*[ \t*&\n]+)+"
            r"([A-Za-z_]\w*)\s*\([^;{}]*\)[^;{}]*\{"
        )
    else:
        return []
    symbols = []
    for match in re.finditer(pattern, code):
        if match[1] in {"if", "for", "while", "switch"}:
            continue
        end = match.end()
        depth = 1
        while end < len(code) and depth:
            depth += (code[end] == "{") - (code[end] == "}")
            end += 1
        attributes = re.split(r"[{};]", code[max(0, match.start() - 200) : match.start()])[-1]
        symbols.append(
            {
                "name": match[1],
                "line": code.count("\n", 0, match.start(1)) + 1,
                "end_line": code.count("\n", 0, end) + 1,
                "role": "harness"
                if re.search(r"#\s*\[\s*kani::proof\s*]", attributes)
                else "test"
                if re.search(r"#\s*\[\s*test\s*]", attributes)
                else "production",
            }
        )
    return symbols


def inspect_source(text: str, language: str, patterns: dict[str, str]) -> tuple[list, list]:
    code = code_view(text, language)
    symbols = definitions(code, language)
    signals = []
    seen = set()
    for number, line in enumerate(code.splitlines(), 1):
        symbol = next((entry["name"] for entry in symbols if entry["line"] <= number <= entry["end_line"]), None)
        for kind, pattern in patterns.items():
            if kind == "function" and language in {"rust", "c", "cpp"}:
                found = any(entry["line"] == number for entry in symbols)
            else:
                found = bool(re.search(pattern, line))
            if not found:
                continue
            if kind == "ffi" and language in {"c", "cpp"} and re.search(r'\bextern\s+"', line):
                kind = "linkage"
            key = (kind, symbol)
            if key not in seen:
                seen.add(key)
                signals.append({"kind": kind, "line": number, "symbol": symbol, "basis": "heuristic"})
        if language in {"c", "cpp"} and re.search(r"\bextern\s+(?!\")", line) and "(" in line:
            key = ("ffi", symbol)
            if key not in seen:
                seen.add(key)
                signals.append({"kind": "ffi", "line": number, "symbol": symbol, "basis": "heuristic"})
    return signals, symbols
