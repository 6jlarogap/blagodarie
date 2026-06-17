#!/usr/bin/env python3
"""Generate CODE_INDEX.md files with symbol offsets and row counts.

This adopts the 6jlarogap/code-index-md idea for this Django/Python repo:
keep CODE_INDEX.md as the first navigation map, but add precise symbol
locations that let agents read only the relevant fragment.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


MARKER_START = "<!-- CODE_INDEX_SYMBOLS_START -->"
MARKER_END = "<!-- CODE_INDEX_SYMBOLS_END -->"
GENERATED_NOTE = "Auto-generated symbol index. Do not edit this section manually."

INDEXABLE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".java", ".md", ".sh"}
EXCLUDED_DIR_NAMES = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "ENV",
    "media",
    "migrations",
    "node_modules",
    "telegram-bot-api",
    "tmp",
    "venv",
    "venv-app",
}
EXCLUDED_PATH_PREFIXES = (
    "app/static/",
    "audit/",
    "frontend/graph_npm/dist/",
    "frontend/map_npm/dist/",
    "frontend/mgraph/dist/",
)


@dataclass(frozen=True)
class Symbol:
    label: str
    offset: int
    rows: int


@dataclass
class FileIndex:
    path: Path
    rel: str
    lines: int
    symbols: list[Symbol]


def repo_root() -> Path:
    return Path(os.environ.get("CODE_INDEX_ROOT", ".")).resolve()


def is_excluded(rel: str) -> bool:
    rel_posix = rel.replace(os.sep, "/")
    if rel_posix == "CODE_INDEX.md" or rel_posix.endswith("/CODE_INDEX.md"):
        return True
    if any(rel_posix.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return True
    parts = set(Path(rel_posix).parts)
    return bool(parts & EXCLUDED_DIR_NAMES)


def is_indexable(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    if is_excluded(rel):
        return False
    if path.suffix not in INDEXABLE_SUFFIXES:
        return False
    if path.name.endswith(".min.js"):
        return False
    if path.name.lower().startswith("d3") and path.suffix in {".js", ".mjs", ".cjs"}:
        return False
    return True


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()


def row_count(lines: list[str], start: int, end: int | None = None) -> int:
    if end is None:
        end = len(lines)
    return max(1, end - start + 1)


def symbols_by_next(symbols: list[tuple[str, int]], lines: list[str]) -> list[Symbol]:
    out: list[Symbol] = []
    for index, (label, offset) in enumerate(symbols):
        next_offset = symbols[index + 1][1] if index + 1 < len(symbols) else len(lines) + 1
        out.append(Symbol(label=label, offset=offset, rows=max(1, next_offset - offset)))
    return out


class PythonVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.symbols: list[Symbol] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        name = ".".join(self.stack + [node.name])
        rows = row_count([], node.lineno, getattr(node, "end_lineno", node.lineno))
        self.symbols.append(Symbol(f"class {name}", node.lineno, rows))
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node, "def")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node, "async def")

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, kind: str) -> None:
        name = ".".join(self.stack + [node.name])
        rows = row_count([], node.lineno, getattr(node, "end_lineno", node.lineno))
        self.symbols.append(Symbol(f"{kind} {name}", node.lineno, rows))
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()


def index_python(path: Path, lines: list[str]) -> list[Symbol]:
    text = "\n".join(lines) + "\n"
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        fallback: list[tuple[str, int]] = []
        for idx, line in enumerate(lines, start=1):
            match = re.match(r"^\s*(async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
            if match:
                fallback.append((f"{match.group(1)} {match.group(2)}", idx))
        return symbols_by_next(fallback, lines)

    visitor = PythonVisitor()
    visitor.visit(tree)
    return sorted(visitor.symbols, key=lambda item: (item.offset, item.label))


JS_PATTERNS = (
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
    re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*"
        r"(?:async\s*)?(?:function\s*\(|\([^)]*\)\s*=>|[A-Za-z_$][A-Za-z0-9_$]*\s*=>)"
    ),
    re.compile(r"^\s*(?:async\s+)?([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*\{"),
)


def index_js(lines: list[str]) -> list[Symbol]:
    found: list[tuple[str, int]] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("*"):
            continue
        for pattern in JS_PATTERNS:
            match = pattern.match(line)
            if match:
                name = match.group(1)
                if name not in {"if", "for", "while", "switch", "catch", "function"}:
                    found.append((name, idx))
                break
    return symbols_by_next(found, lines)


JAVA_PATTERNS = (
    re.compile(r"^\s*(?:public\s+)?(?:abstract\s+|final\s+)?(?:class|interface|enum)\s+([A-Za-z_$][A-Za-z0-9_$]*)"),
    re.compile(
        r"^\s*(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?"
        r"[A-Za-z_$][A-Za-z0-9_$<>\[\], ?]*\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("
    ),
)


def index_java(lines: list[str]) -> list[Symbol]:
    found: list[tuple[str, int]] = []
    for idx, line in enumerate(lines, start=1):
        if line.strip().startswith("@"):
            continue
        for pattern in JAVA_PATTERNS:
            match = pattern.match(line)
            if match:
                found.append((match.group(1), idx))
                break
    return symbols_by_next(found, lines)


def index_markdown(lines: list[str]) -> list[Symbol]:
    headings: list[tuple[str, int, int]] = []
    for idx, line in enumerate(lines, start=1):
        match = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
        if match:
            headings.append((line.strip(), idx, len(match.group(1))))

    symbols: list[Symbol] = []
    for index, (label, offset, level) in enumerate(headings):
        end = len(lines) + 1
        for _, next_offset, next_level in headings[index + 1 :]:
            if next_level <= level:
                end = next_offset
                break
        symbols.append(Symbol(label, offset, max(1, end - offset)))
    return symbols


SHELL_PATTERNS = (
    re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{"),
    re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(\))?\s*\{"),
)


def index_shell(lines: list[str]) -> list[Symbol]:
    found: list[tuple[str, int]] = []
    for idx, line in enumerate(lines, start=1):
        for pattern in SHELL_PATTERNS:
            match = pattern.match(line)
            if match:
                found.append((match.group(1), idx))
                break
    return symbols_by_next(found, lines)


def index_file(path: Path, root: Path) -> FileIndex:
    lines = read_lines(path)
    suffix = path.suffix
    if suffix == ".py":
        symbols = index_python(path, lines)
    elif suffix in {".js", ".mjs", ".cjs"}:
        symbols = index_js(lines)
    elif suffix == ".java":
        symbols = index_java(lines)
    elif suffix == ".md":
        symbols = index_markdown(lines)
    elif suffix == ".sh":
        symbols = index_shell(lines)
    else:
        symbols = []
    rel = path.relative_to(root).as_posix()
    return FileIndex(path=path, rel=rel, lines=len(lines), symbols=symbols)


def discover_files(root: Path) -> list[FileIndex]:
    indexes: list[FileIndex] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if is_indexable(path, root):
            indexes.append(index_file(path, root))
    return indexes


def scope_dirs(files: list[FileIndex]) -> set[Path]:
    dirs: set[Path] = {Path(".")}
    for file_index in files:
        parent = Path(file_index.rel).parent
        dirs.add(parent)
        while parent != Path("."):
            parent = parent.parent
            dirs.add(parent)
    return dirs


def direct_child_scopes(scope: Path, scopes: set[Path]) -> list[Path]:
    children = []
    for candidate in scopes:
        if candidate == scope:
            continue
        if candidate.parent == scope:
            children.append(candidate)
    return sorted(children, key=lambda item: item.as_posix())


def direct_files(scope: Path, files: list[FileIndex]) -> list[FileIndex]:
    return [
        file_index
        for file_index in files
        if Path(file_index.rel).parent == scope
    ]


def scope_stats(scope: Path, files: list[FileIndex]) -> tuple[int, int]:
    prefix = "" if scope == Path(".") else scope.as_posix() + "/"
    file_count = 0
    symbol_count = 0
    for file_index in files:
        if scope == Path(".") or file_index.rel.startswith(prefix):
            file_count += 1
            symbol_count += len(file_index.symbols)
    return file_count, symbol_count


def render_file(file_index: FileIndex, scope: Path) -> list[str]:
    rel_from_scope = Path(file_index.rel).name if scope != Path(".") else file_index.rel
    if scope != Path("."):
        rel_from_scope = Path(file_index.rel).relative_to(scope).as_posix()
    lines = [f"### `{rel_from_scope}` ({file_index.lines} lines)"]
    if not file_index.symbols:
        lines.append("- No indexed symbols.")
    else:
        for symbol in file_index.symbols:
            lines.append(f"- `{symbol.label}` offset={symbol.offset} rows={symbol.rows}")
    lines.append("")
    return lines


def render_scope(
    root: Path,
    scope: Path,
    scopes: set[Path],
    files: list[FileIndex],
    timestamp: str,
    root_preamble: str | None = None,
) -> str:
    scope_label = "root" if scope == Path(".") else scope.as_posix()
    file_count, symbol_count = scope_stats(scope, files)
    body: list[str] = []

    if scope == Path(".") and root_preamble:
        body.append(root_preamble.rstrip())
        body.append("")

    body.extend(
        [
            MARKER_START,
            f"> {GENERATED_NOTE}",
            f"> Updated: {timestamp}",
            "> Source: adopted from https://github.com/6jlarogap/code-index-md",
            "> Usage: read entries as `offset=N rows=M`; use rows as the read limit.",
            f"> Scope: {scope_label}; files={file_count}; symbols={symbol_count}",
            "",
            "## Pyramid Subindexes",
        ]
    )

    children = direct_child_scopes(scope, scopes)
    if children:
        for child in children:
            child_files, child_symbols = scope_stats(child, files)
            child_index = child / "CODE_INDEX.md"
            body.append(f"- `{child_index.as_posix()}` files={child_files} symbols={child_symbols}")
    else:
        body.append("- No child subindexes.")
    body.append("")

    files_here = direct_files(scope, files)
    body.append("## Files In This Scope")
    if files_here:
        for file_index in sorted(files_here, key=lambda item: item.rel):
            body.extend(render_file(file_index, scope))
    else:
        body.append("- No direct indexed files; use child subindexes.")
        body.append("")

    body.append(MARKER_END)
    body.append("")
    return "\n".join(body)


def existing_preamble(index_path: Path) -> str:
    if not index_path.exists():
        return "# Code Index\n\nUse this file as the first map for this repository."
    text = index_path.read_text(encoding="utf-8", errors="replace")
    if MARKER_START in text:
        return text.split(MARKER_START, 1)[0].rstrip()
    return text.rstrip()


def write_if_changed(path: Path, content: str) -> bool:
    old = None
    if path.exists():
        old = path.read_text(encoding="utf-8", errors="replace")
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def clean_obsolete_indexes(root: Path, scopes: set[Path]) -> None:
    expected = {root / "CODE_INDEX.md"}
    expected.update(root / scope / "CODE_INDEX.md" for scope in scopes if scope != Path("."))
    for path in root.rglob("CODE_INDEX.md"):
        if path in expected:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if MARKER_START in text and GENERATED_NOTE in text:
            path.unlink()


def generate(root: Path, quiet: bool = False) -> int:
    files = discover_files(root)
    scopes = scope_dirs(files)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    changed = 0

    root_index = root / "CODE_INDEX.md"
    root_preamble = existing_preamble(root_index)
    root_content = render_scope(root, Path("."), scopes, files, timestamp, root_preamble)
    changed += int(write_if_changed(root_index, root_content))

    for scope in sorted(scopes, key=lambda item: item.as_posix()):
        if scope == Path("."):
            continue
        index_path = root / scope / "CODE_INDEX.md"
        content = render_scope(root, scope, scopes, files, timestamp)
        changed += int(write_if_changed(index_path, content))

    clean_obsolete_indexes(root, scopes)
    if not quiet:
        print(
            f"CODE_INDEX.md rebuilt: {len(files)} files, "
            f"{sum(len(item.symbols) for item in files)} symbols, {len(scopes)} scopes, "
            f"{changed} files changed"
        )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Rebuild CODE_INDEX.md pyramid indexes.")
    parser.add_argument("--quiet", action="store_true", help="suppress summary output")
    args = parser.parse_args(argv)
    return generate(repo_root(), quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
