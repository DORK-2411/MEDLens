"""Unit tests for deterministic clinical conflict detector."""

from app.clinical.conflict_detector import detect_conflicts, is_negation_or_empty, normalize_string


class TestConflictDetector:
    """Test suite for detect_conflicts function."""

    def test_empty_and_none_inputs_are_safe(self) -> None:
        """Empty dictionaries and None values should not raise and return empty list."""
        assert detect_conflicts({}, {}) == []
        assert detect_conflicts(None, None) == []
        assert detect_conflicts({"allergies": None}, {"allergies": None}) == []
        assert detect_conflicts({"allergies": []}, {"allergies": []}) == []

    def test_no_conflicts_when_both_agree(self) -> None:
        """Exact or case-insensitive matching positive assertions yield no conflicts."""
        patient = {"allergies": ["Penicillin"], "medications": ["Metformin"]}
        extracted = {
            "allergies": ["Penicillin"],
            "medications": ["Metformin"],
            "document_id": "DOC-1",
        }
        assert detect_conflicts(patient, extracted) == []

    def test_whitespace_and_case_insensitive_matching(self) -> None:
        """Spacing and casing differences are normalized without false-positive conflict."""
        assert normalize_string("  Type   2  Diabetes ") == "type 2 diabetes"
        patient = {"conditions": ["  type 2 diabetes  "]}
        extracted = {"conditions": ["TYPE 2 DIABETES"], "document_id": "DOC-2"}
        assert detect_conflicts(patient, extracted) == []

    def test_allergy_denial_conflict_detected(self) -> None:
        """Patient reports 'no known allergies' while document records an allergy."""
        patient = {"allergies": ["no known allergies"]}
        extracted = {"allergies": ["Penicillin"], "source_document_id": "DOC-LAB-101"}

        conflicts = detect_conflicts(patient, extracted)
        assert len(conflicts) == 1
        assert conflicts[0].field == "allergies"
        assert conflicts[0].patient_reported_value == "no known allergies"
        assert conflicts[0].extracted_value == "Penicillin"
        assert conflicts[0].source_document_id == "DOC-LAB-101"

    def test_medication_denial_with_multiple_extracted_meds(self) -> None:
        """Patient reports 'none' for medications while report lists two medications."""
        patient = {"medications": "none"}
        extracted = {
            "medications": ["Metformin 500mg", "Lisinopril 10mg"],
            "document_id": "DOC-CLINIC-55",
        }

        conflicts = detect_conflicts(patient, extracted)
        assert len(conflicts) == 2
        med_names = {c.extracted_value for c in conflicts}
        assert med_names == {"Metformin 500mg", "Lisinopril 10mg"}
        assert all(c.field == "medications" for c in conflicts)
        assert all(c.source_document_id == "DOC-CLINIC-55" for c in conflicts)

    def test_condition_negation_conflict_detected(self) -> None:
        """Patient reports 'nil' or 'no conditions' while report lists Asthma."""
        patient = {"conditions": ["nil"]}
        extracted = {"conditions": ["Asthma"], "document_id": "DOC-09"}

        conflicts = detect_conflicts(patient, extracted)
        assert len(conflicts) == 1
        assert conflicts[0].field == "conditions"
        assert conflicts[0].extracted_value == "Asthma"

    def test_empty_patient_field_with_positive_extracted_records(self) -> None:
        """Empty patient list handled as absence/none, conflicting with documented findings."""
        patient = {"allergies": []}
        extracted = {"allergies": ["Sulfa"], "document_id": "DOC-77"}

        conflicts = detect_conflicts(patient, extracted)
        assert len(conflicts) == 1
        assert conflicts[0].field == "allergies"
        assert conflicts[0].extracted_value == "Sulfa"

    def test_extracted_denial_with_patient_positive_assertion(self) -> None:
        """Patient reports Penicillin allergy, but extracted report states 'NKDA'."""
        patient = {"allergies": ["Penicillin"]}
        extracted = {"allergies": ["NKDA"], "document_id": "DOC-EMR-01"}

        conflicts = detect_conflicts(patient, extracted)
        assert len(conflicts) == 1
        assert conflicts[0].field == "allergies"
        assert conflicts[0].patient_reported_value == "Penicillin"
        assert conflicts[0].extracted_value == "NKDA"

    def test_duplicate_prevention_in_conflicts(self) -> None:
        """Duplicate or case-equivalent items in extracted history do not produce duplicate conflicts."""
        patient = {"allergies": "none"}
        extracted = {
            "allergies": ["Penicillin", "penicillin", " Penicillin "],
            "document_id": "DOC-DUP",
        }

        conflicts = detect_conflicts(patient, extracted)
        assert len(conflicts) == 1
        assert conflicts[0].extracted_value == "Penicillin"

    def test_various_negation_phrases_recognized(self) -> None:
        """Recognize clinical negation variations as negations."""
        assert is_negation_or_empty("none")
        assert is_negation_or_empty("nil")
        assert is_negation_or_empty("n/a")
        assert is_negation_or_empty("N/A")
        assert is_negation_or_empty("no known drug allergies")
        assert is_negation_or_empty("NKDA")
        assert is_negation_or_empty("denies allergies")
        assert is_negation_or_empty("none reported")
        assert is_negation_or_empty("")
        assert is_negation_or_empty(None)
        assert not is_negation_or_empty("Amoxicillin")
        assert not is_negation_or_empty("Hypertension")
