"""Pure deterministic reference-range comparison engine.

Principle: LLMs extract. Code decides.
No LLM, DB, API, network, external ranges, or unit conversion.
"""

from typing import Literal, Optional


def compare_to_range(
    value: Optional[float],
    range_low: Optional[float],
    range_high: Optional[float],
) -> Literal["LOW", "NORMAL", "HIGH", "UNKNOWN"]:
    """Compare a clinical numerical value against reference range bounds printed in the report.

    Args:
        value: The measured lab value.
        range_low: The lower reference range bound from the document.
        range_high: The upper reference range bound from the document.

    Returns:
        - "UNKNOWN" if value, range_low, or range_high is None.
        - "UNKNOWN" if range_low > range_high (invalid/reversed range).
        - "LOW" if value < range_low.
        - "HIGH" if value > range_high.
        - "NORMAL" if range_low <= value <= range_high (exact boundaries are NORMAL).
    """
    if value is None or range_low is None or range_high is None:
        return "UNKNOWN"

    if range_low > range_high:
        return "UNKNOWN"

    if value < range_low:
        return "LOW"

    if value > range_high:
        return "HIGH"

    return "NORMAL"
