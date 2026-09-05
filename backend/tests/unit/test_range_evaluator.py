"""Comprehensive unit tests for the pure deterministic range evaluator.

Verifies 100% branch coverage and boundary correctness without external dependencies.
"""

import pytest
from app.clinical.range_evaluator import compare_to_range


class TestRangeEvaluator:
    """Test suite for compare_to_range pure function."""

    def test_value_strictly_below_range_returns_low(self) -> None:
        """Values lower than range_low evaluate to LOW."""
        assert compare_to_range(3.9, 4.0, 10.0) == "LOW"
        assert compare_to_range(0.0, 1.0, 5.0) == "LOW"
        assert compare_to_range(-10.0, -5.0, 5.0) == "LOW"

    def test_value_strictly_above_range_returns_high(self) -> None:
        """Values higher than range_high evaluate to HIGH."""
        assert compare_to_range(10.1, 4.0, 10.0) == "HIGH"
        assert compare_to_range(100.0, 10.0, 50.0) == "HIGH"
        assert compare_to_range(6.0, -5.0, 5.0) == "HIGH"

    def test_value_within_range_returns_normal(self) -> None:
        """Values strictly inside [range_low, range_high] evaluate to NORMAL."""
        assert compare_to_range(5.0, 4.0, 10.0) == "NORMAL"
        assert compare_to_range(7.5, 4.0, 10.0) == "NORMAL"
        assert compare_to_range(0.0, -2.0, 2.0) == "NORMAL"

    def test_exact_lower_boundary_is_normal(self) -> None:
        """Exact lower boundary (value == range_low) evaluates to NORMAL."""
        assert compare_to_range(4.0, 4.0, 10.0) == "NORMAL"
        assert compare_to_range(-2.0, -2.0, 2.0) == "NORMAL"
        assert compare_to_range(0.0, 0.0, 1.0) == "NORMAL"

    def test_exact_upper_boundary_is_normal(self) -> None:
        """Exact upper boundary (value == range_high) evaluates to NORMAL."""
        assert compare_to_range(10.0, 4.0, 10.0) == "NORMAL"
        assert compare_to_range(2.0, -2.0, 2.0) == "NORMAL"
        assert compare_to_range(1.0, 0.0, 1.0) == "NORMAL"

    def test_missing_value_returns_unknown(self) -> None:
        """Missing value (None) evaluates to UNKNOWN."""
        assert compare_to_range(None, 4.0, 10.0) == "UNKNOWN"

    def test_missing_range_low_returns_unknown(self) -> None:
        """Missing lower bound (None) evaluates to UNKNOWN."""
        assert compare_to_range(5.0, None, 10.0) == "UNKNOWN"

    def test_missing_range_high_returns_unknown(self) -> None:
        """Missing upper bound (None) evaluates to UNKNOWN."""
        assert compare_to_range(5.0, 4.0, None) == "UNKNOWN"

    def test_all_none_returns_unknown(self) -> None:
        """All parameters None evaluates to UNKNOWN."""
        assert compare_to_range(None, None, None) == "UNKNOWN"

    def test_reversed_range_returns_unknown(self) -> None:
        """Malformed report where range_low > range_high evaluates to UNKNOWN."""
        assert compare_to_range(5.0, 10.0, 4.0) == "UNKNOWN"
        assert compare_to_range(3.0, 10.0, 4.0) == "UNKNOWN"
        assert compare_to_range(15.0, 10.0, 4.0) == "UNKNOWN"

    def test_single_point_range_low_equals_high(self) -> None:
        """Equal bounds (range_low == range_high) handled correctly."""
        assert compare_to_range(5.0, 5.0, 5.0) == "NORMAL"
        assert compare_to_range(4.99, 5.0, 5.0) == "LOW"
        assert compare_to_range(5.01, 5.0, 5.0) == "HIGH"

    def test_negative_ranges_clinical_base_excess(self) -> None:
        """Legitimate negative values (e.g. arterial blood gas base excess) compare correctly."""
        assert compare_to_range(-4.0, -2.0, 2.0) == "LOW"
        assert compare_to_range(-2.0, -2.0, 2.0) == "NORMAL"
        assert compare_to_range(0.0, -2.0, 2.0) == "NORMAL"
        assert compare_to_range(2.0, -2.0, 2.0) == "NORMAL"
        assert compare_to_range(3.5, -2.0, 2.0) == "HIGH"
