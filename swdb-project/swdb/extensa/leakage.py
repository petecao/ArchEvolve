# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/a5/leakage.py (patterns and scan unchanged)
"""Detection of performance-outcome claims in text that must stay outcome-free.

SWDB use (2026-10-03 ET): the free-text explanation of Extensa-mode feedback and the
text a candidate patch adds. The evaluator's numbers reach the provider only as
structured feedback fields (decision D8), never as prose. The rule is refusal, never
redaction: this module finds claims; callers refuse.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["SANITIZER_VERSION", "OutcomeClaim", "find_outcome_claims", "scan_patch_additions",
           "PATTERN_NAMES"]

SANITIZER_VERSION = "a5.outcome_claim_sanitizer.v1"

_DURATION = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:s|sec|secs|second|seconds|ms|msec|millisecond|"
    r"milliseconds|us|usec|microsecond|microseconds|ns|nanosecond|"
    r"nanoseconds|cycles)\b",
    re.IGNORECASE,
)
_RATIO = re.compile(r"\b\d+(?:\.\d+)?\s*[x×](?![\w])", re.IGNORECASE)
_PERCENT = re.compile(r"\b\d+(?:\.\d+)?\s*%")
_VERDICT_WORDS = re.compile(
    r"\b(?:speedup|speed-up|speedups|faster|slower|slowdown|outperform\w*|"
    r"profitab\w*|unprofitab\w*|winner|winning|won the|adopted|adoption|"
    r"regression|regressed|improvement of|improved by|wall[- ]?clock time|"
    r"runtime of|baseline time|median time|confidence interval|p-value)\b",
    re.IGNORECASE,
)

PATTERN_NAMES: tuple[str, ...] = (
    "duration_magnitude", "ratio_multiplier", "percent_magnitude", "outcome_vocabulary",
)
_PATTERNS = (
    ("duration_magnitude", _DURATION),
    ("ratio_multiplier", _RATIO),
    ("percent_magnitude", _PERCENT),
    ("outcome_vocabulary", _VERDICT_WORDS),
)


@dataclass(frozen=True)
class OutcomeClaim:
    pattern: str
    evidence: str
    where: str
    line: int

    def to_dict(self) -> dict:
        return {"pattern": self.pattern, "evidence": self.evidence, "where": self.where, "line": self.line}


def find_outcome_claims(text: str, *, where: str = "") -> tuple[OutcomeClaim, ...]:
    if not text:
        return ()
    found: list[OutcomeClaim] = []
    for line_no, line in enumerate(text.splitlines() or [text], start=1):
        for name, pattern in _PATTERNS:
            for match in pattern.finditer(line):
                found.append(OutcomeClaim(name, match.group(0).strip(), where, line_no))
    return tuple(found)


def _added_lines(patch_text: str) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    current = ""
    for idx, raw in enumerate(patch_text.splitlines(), start=1):
        if raw.startswith("+++ "):
            current = raw[4:].strip()
            if current.startswith("b/"):
                current = current[2:]
            continue
        if raw.startswith("--- ") or raw.startswith("@@"):
            continue
        if raw.startswith("+"):
            out.append((idx, current, raw[1:]))
    return out


def scan_patch_additions(patch_text: str) -> tuple[OutcomeClaim, ...]:
    """Outcome claims in the lines a candidate patch adds, and in new paths."""
    claims: list[OutcomeClaim] = []
    seen_paths: set[str] = set()
    for line_no, path, content in _added_lines(patch_text):
        if path and path not in seen_paths:
            seen_paths.add(path)
            spaced = re.sub(r"[_\-/.]+", " ", path)
            claims.extend(OutcomeClaim(c.pattern, c.evidence, f"path:{path}", line_no)
                          for c in find_outcome_claims(spaced))
        for claim in find_outcome_claims(content):
            claims.append(OutcomeClaim(claim.pattern, claim.evidence, path or "patch", line_no))
    return tuple(claims)
