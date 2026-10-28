"""Build a PR plan (branch, title, body) from a scan report.

This only prints / writes a plan for a human to review. It never calls
GitHub and never submits anything.

Usage:
    python -m bot.plan_pr --report out/report.json --repo owner/name [--out plan.md]
"""
from __future__ import annotations

import argparse
import json
import sys

from bot.typo_logic import is_safe_change

BODY_TEMPLATE = """## Summary

Fix documentation typos only. No code, configuration or meaning changes.

{changes}

## Checklist for the submitter (fill before opening the PR)

- [ ] I read the target repository's CONTRIBUTING guide and PR template
- [ ] Every changed line was reviewed by a human in the diff
- [ ] The change is limited to documentation files
- [ ] No similar open PR exists for the same fixes

This fix was prepared with the help of a small typo-scanning tool and
reviewed manually before submission.
"""


def build_plan(report: dict, repo: str) -> tuple[str, bool]:
    files = report.get("files", [])
    total = report.get("total_matches", 0)
    safe = is_safe_change(len(files), total)
    lines = []
    lines.append(f"# PR plan for {repo}")
    lines.append("")
    lines.append(f"- files: {len(files)}")
    lines.append(f"- total typo fixes: {total}")
    lines.append(f"- within safety limits (<=3 files, <=20 fixes): {'yes' if safe else 'NO - split or drop this candidate'}")
    lines.append("")
    lines.append("## Branch")
    lines.append("")
    lines.append("`docs/fix-typos-prbot`")
    lines.append("")
    lines.append("## Title")
    lines.append("")
    lines.append("`docs: fix typos`")
    lines.append("")
    lines.append("## Body")
    lines.append("")
    changes = "\n".join(
        f"- `{e['path']}`: " + ", ".join(f"{m['typo']} -> {m['correction']}" for m in e["matches"])
        for e in files
    ) or "- (no changes)"
    lines.append(BODY_TEMPLATE.format(changes=changes))
    return "\n".join(lines), safe


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PRbot PR plan builder (no submission)")
    ap.add_argument("--report", required=True)
    ap.add_argument("--repo", required=True, help="owner/name of the target repository")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    with open(args.report, encoding="utf-8") as f:
        report = json.load(f)
    plan, safe = build_plan(report, args.repo)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(plan + "\n")
        print(f"plan written: {args.out}")
    else:
        print(plan)
    if not safe:
        print("warning: this candidate exceeds the safety limits; do not submit as-is", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
