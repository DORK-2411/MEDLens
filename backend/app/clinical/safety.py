"""Lightweight deterministic safety guardrails for AI summaries and clinical outputs.

Detects unauthorized diagnostic and prescriptive phrasing.
No LLM, DB, or API calls.
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field


class SafetyCheckResult(BaseModel):
    """Result of clinical safety guardrail check on generated text."""

    safe: bool = Field(
        description="True if no prohibited diagnostic/prescriptive phrasing was detected",
    )
    violations: List[str] = Field(
        default_factory=list,
        description="List of detected safety violation descriptions or matched phrases",
    )


PROHIBITED_PATTERNS = [
    (r"\byou have\b", "Prohibited diagnostic assertion: 'you have <condition>'"),
    (r"\bdiagnosed with\b", "Prohibited diagnostic statement: 'diagnosed with'"),
    (r"\byou should take\b", "Prohibited prescriptive recommendation: 'you should take'"),
    (r"\bincrease your dose\b", "Prohibited medication dosage alteration: 'increase your dose'"),
    (r"\bdecrease your dose\b", "Prohibited medication dosage alteration: 'decrease your dose'"),
    (r"\bstop taking\b", "Prohibited medication instruction: 'stop taking'"),
    (r"\bstart taking\b", "Prohibited medication instruction: 'start taking'"),
    (r"\bprescribe\w*\b", "Prohibited prescription directive: 'prescribe'"),
]


def check_safety(text: Optional[str]) -> SafetyCheckResult:
    """Scan text for obvious diagnostic or prescriptive language.

    Case-insensitive deterministic check.

    Args:
        text: Plain-text string to evaluate (e.g. AI-generated summary).

    Returns:
        SafetyCheckResult with `safe: bool` and list of violations.
    """
    if not text or not isinstance(text, str):
        return SafetyCheckResult(safe=True, violations=[])

    violations: List[str] = []
    text_lower = text.lower()

    for pattern, description in PROHIBITED_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            violations.append(description)

    return SafetyCheckResult(
        safe=len(violations) == 0,
        violations=violations,
    )
