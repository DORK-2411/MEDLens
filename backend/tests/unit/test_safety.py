"""Unit tests for deterministic safety guardrails."""

from app.clinical.safety import check_safety


class TestSafetyChecker:
    """Test suite for check_safety deterministic guardrail."""

    def test_safe_non_prescriptive_text_passes(self) -> None:
        """Safe informational summaries pass without violations."""
        text = (
            "The patient's hemoglobin A1c is slightly above the reference range. "
            "These findings may be worth discussing with a physician."
        )
        result = check_safety(text)
        assert result.safe is True
        assert len(result.violations) == 0

    def test_detects_you_have_condition(self) -> None:
        """Flags 'you have <condition>' diagnostic assertion."""
        result = check_safety("Based on these observations, you have diabetes.")
        assert result.safe is False
        assert any("you have" in v for v in result.violations)

    def test_detects_diagnosed_with(self) -> None:
        """Flags 'diagnosed with' language."""
        result = check_safety("The patient is diagnosed with anemia.")
        assert result.safe is False
        assert any("diagnosed with" in v for v in result.violations)

    def test_detects_you_should_take(self) -> None:
        """Flags 'you should take' prescriptive advice."""
        result = check_safety("You should take 500mg of acetaminophen for the pain.")
        assert result.safe is False
        assert any("you should take" in v for v in result.violations)

    def test_detects_dosage_alterations(self) -> None:
        """Flags 'increase your dose' and 'decrease your dose' directives."""
        inc_res = check_safety("You may need to increase your dose of lisinopril.")
        assert inc_res.safe is False
        assert any("increase your dose" in v for v in inc_res.violations)

        dec_res = check_safety("Please decrease your dose until symptoms subside.")
        assert dec_res.safe is False
        assert any("decrease your dose" in v for v in dec_res.violations)

    def test_detects_start_and_stop_taking(self) -> None:
        """Flags directives to start or stop taking medications."""
        stop_res = check_safety("Immediately stop taking your blood pressure pills.")
        assert stop_res.safe is False
        assert any("stop taking" in v for v in stop_res.violations)

        start_res = check_safety("You must start taking insulin today.")
        assert start_res.safe is False
        assert any("start taking" in v for v in start_res.violations)

    def test_detects_prescribe_variations(self) -> None:
        """Flags 'prescribe' and related variants."""
        res1 = check_safety("We prescribe antibiotics for this condition.")
        assert res1.safe is False
        assert any("prescribe" in v for v in res1.violations)

        res2 = check_safety("The clinic prescribed a new regimen.")
        assert res2.safe is False

    def test_case_insensitivity(self) -> None:
        """Case variations (ALL-CAPS, Mixed Case) are caught."""
        res1 = check_safety("YOU HAVE HYPERTENSION")
        assert res1.safe is False

        res2 = check_safety("YOU SHOULD TAKE ASPIRIN")
        assert res2.safe is False

    def test_empty_and_none_text_is_safe(self) -> None:
        """Empty or None text evaluates to safe without raising."""
        assert check_safety("").safe is True
        assert check_safety(None).safe is True
        assert check_safety("   ").safe is True

    def test_multiple_violations_captured(self) -> None:
        """Multiple violations in a single text are all captured."""
        text = "You have asthma and you should take steroids. Also stop taking aspirin."
        result = check_safety(text)
        assert result.safe is False
        assert len(result.violations) >= 3
