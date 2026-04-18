#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amalgamate C++ sources into a single submission file for AtCoder-style contests.

Features:
- Starts from an entry .cpp (e.g., src/main.cpp) and expands only local includes: #include "path"
- Keeps system includes: #include <...> as-is (optionally deduplicated & moved to top)
- Prevents multiple expansion of the same file (even without include guards)
- Adds section markers for readability

Limitations (by design):
- Only expands literal includes: #include "foo.hpp" (no macros in include path)
- If your project relies on conditional includes to change content, this script follows the entry's path.
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Tuple, Optional


INC_LOCAL_RE = re.compile(r'^\s*#\s*include\s*"([^"]+)"\s*$')
INC_SYS_RE = re.compile(r'^\s*#\s*include\s*<([^>]+)>\s*$')

PRAGMA_ONCE_RE = re.compile(r'^\s*#\s*pragma\s+once\s*$')


@dataclass
class Options:
    root: Path
    entry: Path
    out: Path
    keep_comments: bool
    move_system_includes_to_top: bool
    dedup_system_includes: bool
    add_section_markers: bool
    add_line_directives: bool  # helps debugging, but may be noisy on AtCoder
    strip_pragma_once_and_guards: bool  # optional cleanup


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _norm(p: Path) -> Path:
    # absolute normalized path (resolves .. but keeps symlinks as-is)
    return p.resolve()


def _is_under_root(p: Path, root: Path) -> bool:
    try:
        _ = p.relative_to(root)
        return True
    except ValueError:
        return False


def _detect_include_guard(lines: List[str]) -> Optional[Tuple[int, int]]:
    """
    Very small heuristic:
      #ifndef XXX
      #define XXX
      ...
      #endif
    Returns (start_index, end_index_inclusive) if found, else None.
    """
    if len(lines) < 3:
        return None
    i = 0
    # skip leading blank lines / comments
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith("//")):
        i += 1
    if i + 1 >= len(lines):
        return None

    m1 = re.match(r'^\s*#\s*ifndef\s+([A-Za-z_]\w*)\s*$', lines[i])
    if not m1:
        return None
    macro = m1.group(1)
    m2 = re.match(r'^\s*#\s*define\s+%s\s*$' % re.escape(macro), lines[i + 1])
    if not m2:
        return None

    # find matching #endif near end (ignore nested complexity; good enough for typical guards)
    # scan from bottom up
    j = len(lines) - 1
    while j > i + 1 and lines[j].strip() == "":
        j -= 1
    if j <= i + 1:
        return None
    if not re.match(r'^\s*#\s*endif\b', lines[j]):
        return None
    return (i, j)


def amalgamate(opts: Options) -> None:
    visited: Set[Path] = set()
    system_includes: List[str] = []
    system_seen: Set[str] = set()

    out_lines: List[str] = []

    def emit(line: str) -> None:
        out_lines.append(line)

    def add_system_include(line: str) -> None:
        if opts.dedup_system_includes:
            if line in system_seen:
                return
            system_seen.add(line)
        system_includes.append(line)

    def expand_file(file_path: Path, including_from: Optional[Path]) -> None:
        abs_path = _norm(file_path)

        if not _is_under_root(abs_path, opts.root):
            # Safety: don't inline outside root (prevents accidental secret leakage)
            raise RuntimeError(
                f"Refusing to inline file outside root.\n"
                f"  root: {opts.root}\n"
                f"  file: {abs_path}\n"
                f"  included from: {including_from}"
            )

        if abs_path in visited:
            return
        visited.add(abs_path)

        text = _read_text(abs_path)
        lines = text.splitlines()

        if opts.add_section_markers:
            emit("")
            emit(f"// ===== BEGIN: {abs_path.relative_to(opts.root).as_posix()} =====")
        if opts.add_line_directives:
            # GCC/Clang accept #line, but it can be noisy; keep optional
            emit(f'#line 1 "{abs_path.relative_to(opts.root).as_posix()}"')

        # Optional cleanup: drop pragma once and include guard wrapper
        guard_span = _detect_include_guard(lines) if opts.strip_pragma_once_and_guards else None

        for idx, raw in enumerate(lines):
            # skip guard wrapper lines if detected
            if guard_span is not None:
                s, e = guard_span
                if idx == s or idx == s + 1 or idx == e:
                    continue

            if opts.strip_pragma_once_and_guards and PRAGMA_ONCE_RE.match(raw):
                continue

            m_local = INC_LOCAL_RE.match(raw)
            if m_local:
                inc = m_local.group(1)
                inc_path = (abs_path.parent / inc).resolve()
                if not inc_path.exists():
                    # Try from root as fallback if include uses project-root relative
                    alt = (opts.root / inc).resolve()
                    if alt.exists():
                        inc_path = alt
                    else:
                        raise FileNotFoundError(
                            f'Include not found: "{inc}"\n'
                            f"  in: {abs_path}\n"
                            f"  tried: {abs_path.parent / inc}\n"
                            f"  tried: {opts.root / inc}"
                        )
                expand_file(inc_path, including_from=abs_path)
                continue

            m_sys = INC_SYS_RE.match(raw)
            if m_sys:
                if opts.move_system_includes_to_top:
                    add_system_include(raw.strip())
                else:
                    emit(raw)
                continue

            # Optionally drop full-line comments
            if not opts.keep_comments:
                stripped = raw.lstrip()
                if stripped.startswith("//"):
                    continue

            emit(raw)

        if opts.add_section_markers:
            emit(f"// ===== END:   {abs_path.relative_to(opts.root).as_posix()} =====")
            emit("")

    # Header
    emit("// Auto-generated by tools/amalgamate.py. DO NOT EDIT THIS FILE DIRECTLY.")
    emit("// Source entry: " + opts.entry.as_posix())
    emit("")

    expand_file((opts.root / opts.entry).resolve(), including_from=None)

    # If we moved system includes to top, put them at the very top (after the banner)
    if opts.move_system_includes_to_top and system_includes:
        # remove duplicates already done in add_system_include (if enabled)
        # Insert after banner lines (currently 3 lines: 2 comment + blank)
        insert_at = 3
        merged = [*system_includes, ""]
        out_lines[insert_at:insert_at] = merged

    opts.out.parent.mkdir(parents=True, exist_ok=True)
    opts.out.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Amalgamate C++ project into single .cpp")
    ap.add_argument("--root", default=".", help="Project root directory (default: .)")
    ap.add_argument("--entry", required=True, help="Entry .cpp path (relative to root), e.g. src/main.cpp")
    ap.add_argument("--out", required=True, help="Output file path, e.g. submit/main.cpp")
    ap.add_argument("--keep-comments", action="store_true", help="Keep // line comments (default: drop)")
    ap.add_argument("--no-move-system-includes", action="store_true",
                    help="Do not move #include <...> to top (default: move to top)")
    ap.add_argument("--no-dedup-system-includes", action="store_true",
                    help="Do not deduplicate #include <...> (default: dedup)")
    ap.add_argument("--no-section-markers", action="store_true",
                    help="Do not add BEGIN/END section markers")
    ap.add_argument("--line-directives", action="store_true",
                    help='Add #line directives (useful for debugging)')
    ap.add_argument("--strip-guards", action="store_true",
                    help="Strip #pragma once and simple include guards when inlining")
    args = ap.parse_args()

    opts = Options(
        root=Path(args.root).resolve(),
        entry=Path(args.entry),
        out=Path(args.out),
        keep_comments=bool(args.keep_comments),
        move_system_includes_to_top=not bool(args.no_move_system_includes),
        dedup_system_includes=not bool(args.no_dedup_system_includes),
        add_section_markers=not bool(args.no_section_markers),
        add_line_directives=bool(args.line_directives),
        strip_pragma_once_and_guards=bool(args.strip_guards),
    )

    amalgamate(opts)


if __name__ == "__main__":
    main()
