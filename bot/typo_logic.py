"""Pure typo-detection logic for documentation files.

No network, no file writes. Everything here is testable in isolation.

Safety rules baked in:
- Only documentation files are eligible.
- Fenced code blocks, inline code and URLs are never rewritten.
- A change is "safe" only when it is small: few files, few lines.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict

DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt", ".adoc"}
EXCLUDED_PARTS = {"node_modules", ".git", "vendor", "dist", "build", ".venv"}

# A URL (scheme://...) or a bare www. link; the whole match is protected.
_URL_RE = re.compile(r"(?:https?|ftp)://[^\s)\]>]+|www\.[^\s)\]>]+")
# Inline code spans in backticks.
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


@dataclass
class TypoMatch:
    line: int        # 1-based
    column: int      # 1-based
    typo: str
    correction: str
    context: str     # the original line, stripped

    def to_dict(self):
        return asdict(self)


def is_doc_file(path: str) -> bool:
    parts = [p for p in path.replace("\\", "/").split("/") if p]
    if any(p in EXCLUDED_PARTS for p in parts):
        return False
    name = parts[-1] if parts else ""
    dot = name.rfind(".")
    if dot < 0:
        return False
    return name[dot:].lower() in DOC_EXTENSIONS


def validate_dictionary(dictionary: dict) -> list[str]:
    """Return a list of problems; empty means the dictionary is usable."""
    problems = []
    seen = {}
    for typo, correction in dictionary.items():
        if not isinstance(typo, str) or not isinstance(correction, str):
            problems.append(f"non-string entry: {typo!r}")
            continue
        if not typo or not correction:
            problems.append(f"empty entry: {typo!r}")
        if typo == correction:
            problems.append(f"typo equals correction: {typo!r}")
        key = typo.lower()
        if key in seen:
            problems.append(f"duplicate typo (case-insensitive): {typo!r}")
        seen[key] = correction
        # A correction must not itself be a known typo, or fixes could chain.
        if correction.lower() in seen and correction.lower() != key:
            pass  # order-dependent; the exact check below covers the final dict
    for typo, correction in dictionary.items():
        if correction in dictionary and correction != typo:
            problems.append(f"correction is itself a typo key: {typo!r} -> {correction!r}")
    return problems


def load_dictionary(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("dictionary must be a JSON object of typo -> correction")
    problems = validate_dictionary(data)
    if problems:
        raise ValueError("invalid dictionary: " + "; ".join(problems))
    return data


def _protected_spans(line: str) -> list[tuple[int, int]]:
    spans = []
    for rx in (_URL_RE, _INLINE_CODE_RE):
        for m in rx.finditer(line):
            spans.append((m.start(), m.end()))
    return spans


def _in_spans(pos: int, length: int, spans) -> bool:
    end = pos + length
    return any(pos < s_end and end > s_start for s_start, s_end in spans)


def _compile(dictionary: dict):
    # Longest typo first so overlapping entries prefer the longer match.
    keys = sorted(dictionary, key=len, reverse=True)
    if not keys:
        return None
    pattern = r"\b(?:" + "|".join(re.escape(k) for k in keys) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


def _match_case(original: str, correction: str) -> str:
    if original.isupper():
        return correction.upper()
    if original[:1].isupper():
        return correction[:1].upper() + correction[1:]
    return correction


def find_typos(text: str, dictionary: dict) -> list[TypoMatch]:
    rx = _compile(dictionary)
    if rx is None:
        return []
    matches: list[TypoMatch] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        spans = _protected_spans(line)
        for m in rx.finditer(line):
            if _in_spans(m.start(), len(m.group(0)), spans):
                continue
            typo = m.group(0)
            correction = _match_case(typo, dictionary.get(typo) or dictionary.get(typo.lower()) or "")
            if not correction:
                # Dictionary keys are matched case-insensitively via \b pattern
                # only when the exact key appears; fall back to lower lookup.
                for k, v in dictionary.items():
                    if k.lower() == typo.lower():
                        correction = _match_case(typo, v)
                        break
            if correction:
                matches.append(TypoMatch(lineno, m.start() + 1, typo, correction, line.strip()))
    return matches


def apply_fixes(text: str, dictionary: dict) -> tuple[str, list[TypoMatch]]:
    matches = find_typos(text, dictionary)
    if not matches:
        return text, []
    lines = text.splitlines()
    # Apply per line, right to left so columns stay valid.
    by_line: dict[int, list[TypoMatch]] = {}
    for m in matches:
        by_line.setdefault(m.line, []).append(m)
    for lineno, ms in by_line.items():
        line = lines[lineno - 1]
        for m in sorted(ms, key=lambda x: x.column, reverse=True):
            start = m.column - 1
            line = line[:start] + m.correction + line[start + len(m.typo):]
        lines[lineno - 1] = line
    result = "\n".join(lines)
    if text.endswith("\n"):
        result += "\n"
    return result, matches


def is_safe_change(num_files: int, num_matches: int, max_files: int = 3, max_matches: int = 20) -> bool:
    """Small, reviewable changes only. Anything bigger must be split or dropped."""
    return 1 <= num_files <= max_files and 1 <= num_matches <= max_matches
