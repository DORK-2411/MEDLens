"""Unit tests for patient intake service."""

import pytest
from sqlalchemy.orm import Session

from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.patient_service import (
    create_patient,
    delete_patient,
    get_patient,
    update_patient,
)


class TestPatientService:
    """Test suite for patient_service CRUD functions."""

    def test_create_and_get_patient(self, db_session: Session) -> None:
        """Create a patient and retrieve it by ID."""
        patient_in = PatientCreate(
            patient_id="PAT-001",
            age=45,
            sex="Male",
            symptoms=["Cough", "Fever"],
            conditions=["Asthma"],
            allergies=["Penicillin"],
            medications=["Albuterol"],
            notes="Initial intake report",
        )
        created = create_patient(db=db_session, patient_in=patient_in)

        assert created.patient_id == "PAT-001"
        assert created.age == 45
        assert created.sex == "Male"
        assert created.symptoms == ["Cough", "Fever"]
        assert created.conditions == ["Asthma"]
        assert created.allergies == ["Penicillin"]
        assert created.medications == ["Albuterol"]
        assert created.notes == "Initial intake report"

        # Fetch via get_patient
        fetched = get_patient(db=db_session, patient_id="PAT-001")
        assert fetched is not None
        assert fetched.patient_id == "PAT-001"
        assert fetched.allergies == ["Penicillin"]

    def test_create_patient_auto_generates_id(self, db_session: Session) -> None:
        """Generating patient_id when none is supplied."""
        patient_in = PatientCreate(age=30, sex="Female")
        created = create_patient(db=db_session, patient_in=patient_in)

        assert created.patient_id.startswith("PAT-")
        assert created.age == 30

    def test_create_duplicate_patient_id_raises_error(self, db_session: Session) -> None:
        """Attempting to create duplicate patient_id raises ValueError."""
        patient_in = PatientCreate(patient_id="PAT-DUP", age=25)
        create_patient(db=db_session, patient_in=patient_in)

        with pytest.raises(ValueError, match="already exists"):
            create_patient(db=db_session, patient_in=patient_in)

    def test_update_patient(self, db_session: Session) -> None:
        """Update fields on an existing patient while preserving untouched fields."""
        patient_in = PatientCreate(
            patient_id="PAT-UPDATE",
            age=50,
            sex="Female",
            symptoms=["Headache"],
            allergies=["Aspirin"],
        )
        create_patient(db=db_session, patient_in=patient_in)

        update_in = PatientUpdate(
            age=51,
            symptoms=["Headache", "Nausea"],
            notes="Follow-up added nausea",
        )
        updated = update_patient(
            db=db_session, patient_id="PAT-UPDATE", patient_update=update_in
        )

        assert updated is not None
        assert updated.age == 51
        assert updated.sex == "Female"  # preserved
        assert updated.symptoms == ["Headache", "Nausea"]
        assert updated.allergies == ["Aspirin"]  # preserved
        assert updated.notes == "Follow-up added nausea"

    def test_delete_patient(self, db_session: Session) -> None:
        """Deleting an existing patient returns True and removes it from DB."""
        patient_in = PatientCreate(patient_id="PAT-DEL", age=60)
        create_patient(db=db_session, patient_in=patient_in)

        assert delete_patient(db=db_session, patient_id="PAT-DEL") is True
        assert get_patient(db=db_session, patient_id="PAT-DEL") is None

        # Deleting nonexistent returns False
        assert delete_patient(db=db_session, patient_id="PAT-NONEXISTENT") is False

    def test_multiple_patients_remain_independent(self, db_session: Session) -> None:
        """Multiple patient records do not cross-contaminate list fields."""
        p1 = create_patient(
            db=db_session,
            patient_in=PatientCreate(
                patient_id="PAT-A",
                allergies=["Sulfa"],
                medications=["Metformin"],
            ),
        )
        p2 = create_patient(
            db=db_session,
            patient_in=PatientCreate(
                patient_id="PAT-B",
                allergies=["Latex"],
                medications=["Lisinopril"],
            ),
        )

        fetched_a = get_patient(db=db_session, patient_id="PAT-A")
        fetched_b = get_patient(db=db_session, patient_id="PAT-B")

        assert fetched_a is not None and fetched_b is not None
        assert fetched_a.allergies == ["Sulfa"]
        assert fetched_b.allergies == ["Latex"]
        assert fetched_a.medications == ["Metformin"]
        assert fetched_b.medications == ["Lisinopril"]
