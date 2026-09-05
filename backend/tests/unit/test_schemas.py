"""Unit tests for Pydantic v2 schemas: validation, constraints, and mutable isolation."""

from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.audit import AuditLog
from app.schemas.conflict import Conflict
from app.schemas.observation import Observation
from app.schemas.patient import PatientRecord
from app.schemas.provenance import Provenance
from app.schemas.report import DiagnosticReport


class TestSchemas:
    """Test suite for all Phase 2 Pydantic schemas."""

    def test_provenance_valid_sources(self) -> None:
        """Provenance accepts only allowed literal sources."""
        now = datetime.now(timezone.utc)
        for src in ["user_provided", "ai_extracted", "ai_generated"]:
            prov = Provenance(source=src, extracted_at=now)
            assert prov.source == src

    def test_provenance_rejects_invalid_source(self) -> None:
        """Provenance rejects arbitrary or unknown source literals."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            Provenance(source="web_scraped", extracted_at=now)  # type: ignore

    def test_provenance_confidence_bounds(self) -> None:
        """Confidence must be between 0.0 and 1.0 inclusive."""
        now = datetime.now(timezone.utc)
        # Valid bounds
        assert Provenance(source="ai_extracted", confidence=0.0, extracted_at=now).confidence == 0.0
        assert Provenance(source="ai_extracted", confidence=0.75, extracted_at=now).confidence == 0.75
        assert Provenance(source="ai_extracted", confidence=1.0, extracted_at=now).confidence == 1.0

        # Below 0.0 rejected
        with pytest.raises(ValidationError):
            Provenance(source="ai_extracted", confidence=-0.01, extracted_at=now)

        # Above 1.0 rejected
        with pytest.raises(ValidationError):
            Provenance(source="ai_extracted", confidence=1.01, extracted_at=now)

    def test_observation_flags_valid_and_invalid(self) -> None:
        """Observation accepts only LOW, NORMAL, HIGH, UNKNOWN flags."""
        now = datetime.now(timezone.utc)
        prov = Provenance(source="ai_extracted", confidence=0.9, extracted_at=now)

        for valid_flag in ["LOW", "NORMAL", "HIGH", "UNKNOWN"]:
            obs = Observation(test_name="Glucose", flag=valid_flag, provenance=prov)
            assert obs.flag == valid_flag

        # Invalid flags raise validation error
        with pytest.raises(ValidationError):
            Observation(test_name="Glucose", flag="ABNORMAL", provenance=prov)  # type: ignore

        with pytest.raises(ValidationError):
            Observation(test_name="Glucose", flag="CRITICAL", provenance=prov)  # type: ignore

    def test_observation_requires_provenance(self) -> None:
        """Observation cannot be created without provenance."""
        with pytest.raises(ValidationError):
            Observation(test_name="Potassium")  # type: ignore

    def test_patient_age_validation(self) -> None:
        """PatientRecord enforces non-negative age."""
        # Valid non-negative ages
        assert PatientRecord(patient_id="p1", age=0).age == 0
        assert PatientRecord(patient_id="p2", age=45).age == 45
        assert PatientRecord(patient_id="p3", age=105).age == 105
        assert PatientRecord(patient_id="p4", age=None).age is None

        # Negative age rejected
        with pytest.raises(ValidationError):
            PatientRecord(patient_id="p_bad", age=-1)

        with pytest.raises(ValidationError):
            PatientRecord(patient_id="p_bad2", age=-75)

    def test_mutable_list_isolation(self) -> None:
        """Modifying list fields on one PatientRecord instance must not affect others."""
        patient1 = PatientRecord(patient_id="patient-001")
        patient2 = PatientRecord(patient_id="patient-002")

        # Mutate lists on patient1
        patient1.symptoms.append("Headache")
        patient1.conditions.append("Migraine")
        patient1.allergies.append("Peanuts")
        patient1.medications.append("Ibuprofen")

        now = datetime.now(timezone.utc)
        audit_entry = AuditLog(
            action="verify",
            entity_type="patient",
            entity_id="patient-001",
            edited_by="dr_smith",
            timestamp=now,
        )
        patient1.audit_log.append(audit_entry)

        # Verify patient2 remains isolated and empty
        assert patient2.symptoms == []
        assert patient2.conditions == []
        assert patient2.allergies == []
        assert patient2.medications == []
        assert patient2.reports == []
        assert patient2.audit_log == []

        # Verify patient1 preserved mutations
        assert patient1.symptoms == ["Headache"]
        assert patient1.conditions == ["Migraine"]
        assert patient1.allergies == ["Peanuts"]
        assert patient1.medications == ["Ibuprofen"]
        assert len(patient1.audit_log) == 1

    def test_diagnostic_report_and_observation_nesting(self) -> None:
        """DiagnosticReport nests Observations with clean provenance."""
        now = datetime.now(timezone.utc)
        prov = Provenance(source="ai_extracted", confidence=0.95, extracted_at=now)

        obs = Observation(
            test_name="Hemoglobin A1c",
            value=6.2,
            value_raw="6.2",
            unit="%",
            reference_range_low=4.0,
            reference_range_high=5.6,
            reference_range_raw="4.0 - 5.6",
            flag="HIGH",
            date=date(2026, 9, 1),
            provenance=prov,
        )

        report = DiagnosticReport(
            report_id="rep-1",
            patient_id="pat-1",
            document_id="doc-101",
            observations=[obs],
            provenance=prov,
        )

        assert len(report.observations) == 1
        assert report.observations[0].value == 6.2
        assert report.observations[0].flag == "HIGH"

    def test_conflict_schema(self) -> None:
        """Conflict schema stores discrepancy details."""
        now = datetime.now(timezone.utc)
        conflict = Conflict(
            field="allergies",
            patient_reported_value="No known allergies",
            extracted_value="Penicillin",
            source_document_id="DOC-99",
            detected_at=now,
        )
        assert conflict.field == "allergies"
        assert conflict.extracted_value == "Penicillin"
        assert conflict.source_document_id == "DOC-99"

    def test_audit_log_schema(self) -> None:
        """AuditLog schema correctly records human verification details."""
        now = datetime.now(timezone.utc)
        audit = AuditLog(
            entry_id="audit-123",
            action="edit",
            entity_type="observation",
            entity_id="obs-456",
            field_name="value",
            old_value="5.0",
            new_value="5.2",
            edited_by="clinician_user",
            timestamp=now,
        )
        assert audit.action == "edit"
        assert audit.old_value == "5.0"
        assert audit.new_value == "5.2"
        assert audit.edited_by == "clinician_user"
