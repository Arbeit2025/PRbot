"""Dry-run scanner: walk a local checkout and report doc typos.

Never writes to the scanned tree and never contacts GitHub.
Optionally writes a JSON report to a path the user chooses.

Usage:
    python -m bot.scan_local --root /path/to/checkout [--dict config/typos.json]
                             [--report out/report.json] [--apply-preview DIR]
--apply-preview writes *fixed copies* into DIR for human review; the
original checkout is still untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from bot.typo_logic import apply_fixes, find_typos, is_doc_file, load_dictionary

DEFAULT_DICT = os.path.join(os.path.dirname(__file__), "..", "config", "typos.json")


def scan(root: str, dictionary: dict) -> dict:
    files = []
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", ".venv"}]
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if not is_doc_file(rel):
                continue
            with open(full, encoding="utf-8", errors="strict") as f:
                text = f.read()
            matches = find_typos(text, dictionary)
            if matches:
                files.append({"path": rel, "matches": [m.to_dict() for m in matches]})
                total += len(matches)
    return {"root": os.path.abspath(root), "total_matches": total, "files": files}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PRbot dry-run doc typo scanner")
    ap.add_argument("--root", required=True, help="local checkout to scan")
    ap.add_argument("--dict", default=DEFAULT_DICT, help="typo dictionary JSON")
    ap.add_argument("--report", default=None, help="write JSON report here")
    ap.add_argument("--apply-preview", default=None,
                    help="write fixed copies of matched files into this directory")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        print(f"root is not a directory: {args.root}", file=sys.stderr)
        return 2
    dictionary = load_dictionary(args.dict)
    report = scan(args.root, dictionary)

    print(f"scanned: {report['root']}")
    print(f"files with matches: {len(report['files'])}  total matches: {report['total_matches']}")
    for entry in report["files"]:
        for m in entry["matches"]:
            print(f"  {entry['path']}:{m['line']}:{m['column']}  {m['typo']} -> {m['correction']}")

    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"report written: {args.report}")

    if args.apply_preview:
        for entry in report["files"]:
            src = os.path.join(args.root, entry["path"])
            dst = os.path.join(args.apply_preview, entry["path"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, encoding="utf-8") as f:
                fixed, _ = apply_fixes(f.read(), dictionary)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(fixed)
        print(f"preview copies written: {args.apply_preview} (originals untouched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
