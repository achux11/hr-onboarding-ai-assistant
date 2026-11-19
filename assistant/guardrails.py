"""Questions an assistant should not answer on its own.

These are routed to a person in HR with a category, so the employee gets help
from someone accountable instead of a generated answer.
"""
from __future__ import annotations

import re

SENSITIVE = {
    "harassment_or_discrimination": r"harass|discriminat|racis|sexis|slur|abus|yell|bull(y|ied|ying)|hostile|retaliat|unsafe|threaten",
    "medical_or_accommodation": r"disab|pregnan|medical condition|diagnos|accommodat|mental health|therapy",
    "immigration_or_visa": r"visa|h-?1b|opt\b|work permit|green card|sponsor|immigration",
    "compensation_change": r"raise|negotiat|salary increase|promotion|bonus amount|pay cut",
    "separation_or_discipline": r"\bfired\b|terminat|layoff|laid off|resign|quit|warning letter|disciplin|performance plan|\bpip\b",
    "legal": r"lawyer|lawsuit|\bsue\b|legal action|attorney",
}


def check(question: str) -> str | None:
    """Return the sensitive category for a question, or None if it is safe to answer."""
    text = question.lower()
    for category, pattern in SENSITIVE.items():
        if re.search(pattern, text):
            return category
    return None
