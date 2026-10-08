#!/usr/bin/env python3
"""
archive_sessions.py - Deterministic session log archiver.
Prepends the universal deprecation warning to active session logs and moves them
to docs/sessions/deprecated_archive/ safely and idempotently.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

DEPRECATION_WARNING = """\
> [!WARNING]
> **DEPRECATED ARCHIVE FILE**
> This session log contains outdated context, historical assumptions, and potentially obsolete decisions. It is kept strictly for historical tracking. Do not use this file for LLM decision-making or active context ingestion. Please refer to the consolidated Master files in `docs/sessions/master_findings/` or current documentation for the accurate, verified project state.

"""

def find_sessions_dir(explicit_path=None):
    if explicit_path:
        p = Path(explicit_path).resolve()
        if p.exists() and p.is_dir():
            return p
        raise FileNotFoundError(f"Specified sessions directory not found: {explicit_path}")

    candidates = [
        Path.cwd() / "docs" / "sessions",
        Path.cwd() / "sessions",
        Path.cwd().parent / "docs" / "sessions",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c.resolve()

    curr = Path.cwd().resolve()
    for _ in range(3):
        cand = curr / "docs" / "sessions"
        if cand.exists() and cand.is_dir():
            return cand.resolve()
        curr = curr.parent

    raise FileNotFoundError("Could not locate 'docs/sessions' directory. Please specify with --dir.")

def main():
    parser = argparse.ArgumentParser(description="Archive active session markdown logs into deprecated_archive.")
    parser.add_argument("--dir", help="Path to docs/sessions directory", default=None)
    parser.add_argument("--files", nargs="*", help="Specific session file names or paths to archive (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without modifying or moving files")
    args = parser.parse_args()

    try:
        sessions_dir = find_sessions_dir(args.dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    archive_dir = sessions_dir / "deprecated_archive"
    if not args.dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)

    if args.files:
        candidates = []
        for f in args.files:
            fp = Path(f)
            if not fp.is_absolute():
                fp = sessions_dir / fp
            if fp.exists() and fp.is_file():
                candidates.append(fp)
            else:
                print(f"Warning: Specified file not found: {f}", file=sys.stderr)
    else:
        candidates = [
            f for f in sessions_dir.iterdir()
            if f.is_file() and f.suffix.lower() == ".md"
        ]

    candidates.sort(key=lambda p: p.name)

    if not candidates:
        print(f"No session markdown files found to archive in {sessions_dir}.")
        return

    print(f"Target sessions directory: {sessions_dir}")
    print(f"Destination archive: {archive_dir}")
    print(f"Found {len(candidates)} session file(s) to process:\n")

    processed_count = 0
    for file_path in candidates:
        dest_path = archive_dir / file_path.name
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as err:
            print(f"  [ERROR] reading {file_path.name}: {err}", file=sys.stderr)
            continue

        already_deprecated = (
            "DEPRECATED ARCHIVE FILE" in content or
            content.strip().startswith("> [!WARNING]")
        )

        new_content = content if already_deprecated else (DEPRECATION_WARNING + "\n" + content)

        if args.dry_run:
            print(f"  [DRY-RUN] Would annotate and move: {file_path.name} -> deprecated_archive/")
            processed_count += 1
            continue

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as err:
            print(f"  [ERROR] writing {file_path.name}: {err}", file=sys.stderr)
            continue

        try:
            if dest_path.exists():
                dest_path.unlink()
            shutil.move(str(file_path), str(dest_path))
            print(f"  [ARCHIVED] {file_path.name} -> deprecated_archive/{dest_path.name}")
            processed_count += 1
        except Exception as err:
            print(f"  [ERROR] moving {file_path.name}: {err}", file=sys.stderr)

    print(f"\nSummary: Successfully processed and archived {processed_count}/{len(candidates)} file(s).")

if __name__ == "__main__":
    main()
