from __future__ import annotations

import re
from typing import List

from .trace_schema import LQMCheckResult


_EQUATION_RE = re.compile(r"(\d+)\s*([+\-*/])\s*(\d+)\s*=\s*(\d+)")
_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def verify_numbers(text: str) -> LQMCheckResult:
    verified = 0
    unverified = 0
    flags: list[str] = []
    details: list[str] = []

    for match in _EQUATION_RE.finditer(text):
        a = int(match.group(1))
        op = match.group(2)
        b = int(match.group(3))
        claimed = int(match.group(4))
        if op == "+":
            actual = a + b
        elif op == "-":
            actual = a - b
        elif op == "*":
            actual = a * b
        else:
            actual = a // b if b != 0 else None
        if actual is None or actual != claimed:
            unverified += 1
            flags.append("lqm_equation_mismatch")
            details.append(f"Equation mismatch: {a}{op}{b} != {claimed}")
        else:
            verified += 1

    for match in _PERCENT_RE.finditer(text):
        value = float(match.group(1))
        if value > 100.0:
            unverified += 1
            flags.append("lqm_percent_over_100")
            details.append(f"Percent exceeds 100: {value}%")
        else:
            verified += 1

    return LQMCheckResult(
        verified_count=verified,
        unverified_count=unverified,
        flags=sorted(set(flags)),
        details=details,
    )

