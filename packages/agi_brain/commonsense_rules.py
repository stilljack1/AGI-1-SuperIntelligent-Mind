from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: str
    penalty: float


PHYSICAL_RULES: tuple[Rule, ...] = (
    Rule("physics_fell_up", "fell up", 1.2),
    Rule("physics_no_gravity", "without gravity on earth", 1.0),
    Rule("physics_perpetual_motion", "perpetual motion machine", 1.1),
)

SOCIAL_RULES: tuple[Rule, ...] = (
    Rule("social_insult_cooperation", "insult the customer to improve trust", 1.0),
    Rule("social_threat_compliance", "threaten the user", 1.2),
)

SCRIPT_RULES: tuple[Rule, ...] = (
    Rule("script_ship_before_build", "deploy before building", 0.8),
    Rule("script_pay_before_invoice", "pay before receiving invoice and approval", 0.6),
)


def evaluate_commonsense(text: str) -> Tuple[float, List[str]]:
    lowered = text.lower()
    penalties = 0.0
    flags: list[str] = []
    for rule in (*PHYSICAL_RULES, *SOCIAL_RULES, *SCRIPT_RULES):
        if rule.pattern in lowered:
            penalties += rule.penalty
            flags.append(rule.name)
    return penalties, flags

