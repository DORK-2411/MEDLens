"""Integration tests for patients REST API endpoints."""

from fastapi.testclient import TestClient


class TestPatientsAPI:
    """Test suite for /api/patients API endpoints."""

    def test_create_patient_success(self, client: TestClient) -> None:
        """POST /api/patients creates patient and returns 201 with PatientRecord."""
        payload = {
            "patient_id": "PAT-TEST-01",
            "age": 35,
            "sex": "Female",
            "symptoms": ["Fatigue", "Dizziness"],
            "conditions": ["Hypothyroidism"],
            "allergies": ["Penicillin"],
            "medications": ["Levothyroxine 50mcg"],
            "notes": "Patient reports mild morning fatigue.",
        }
        response = client.post("/api/patients", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["patient_id"] == "PAT-TEST-01"
        assert data["age"] == 35
        assert data["sex"] == "Female"
        assert data["symptoms"] == ["Fatigue", "Dizziness"]
        assert data["conditions"] == ["Hypothyroidism"]
        assert data["allergies"] == ["Penicillin"]
        assert data["medications"] == ["Levothyroxine 50mcg"]
        assert data["notes"] == "Patient reports mild morning fatigue."
        assert data["reports"] == []
        assert data["audit_log"] == []

    def test_get_patient_by_id(self, client: TestClient) -> None:
        """GET /api/patients/{id} retrieves the created record."""
        # Create
        client.post(
            "/api/patients",
            json={"patient_id": "PAT-GET-01", "age": 42, "allergies": ["Aspirin"]},
        )

        # Get
        response = client.get("/api/patients/PAT-GET-01")
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "PAT-GET-01"
        assert data["age"] == 42
        assert data["allergies"] == ["Aspirin"]

    def test_get_nonexistent_patient_returns_404(self, client: TestClient) -> None:
        """GET /api/patients/{id} with invalid ID returns 404."""
        response = client.get("/api/patients/NONEXISTENT-ID")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_patient(self, client: TestClient) -> None:
        """PUT /api/patients/{id} updates fields and preserves untouched ones."""
        # Create
        client.post(
            "/api/patients",
            json={
                "patient_id": "PAT-PUT-01",
                "age": 28,
                "sex": "Male",
                "allergies": ["Peanuts"],
            },
        )

        # Update
        update_payload = {
            "age": 29,
            "symptoms": ["Sore throat"],
        }
        response = client.put("/api/patients/PAT-PUT-01", json=update_payload)
        assert response.status_code == 200

        data = response.json()
        assert data["age"] == 29
        assert data["sex"] == "Male"  # preserved
        assert data["allergies"] == ["Peanuts"]  # preserved
        assert data["symptoms"] == ["Sore throat"]

    def test_update_nonexistent_patient_returns_404(self, client: TestClient) -> None:
        """PUT /api/patients/{id} on nonexistent ID returns 404."""
        response = client.put("/api/patients/NONEXISTENT", json={"age": 50})
        assert response.status_code == 404

    def test_delete_patient(self, client: TestClient) -> None:
        """DELETE /api/patients/{id} deletes the patient and subsequent GET returns 404."""
        # Create
        client.post("/api/patients", json={"patient_id": "PAT-DEL-01", "age": 55})

        # Delete
        del_resp = client.delete("/api/patients/PAT-DEL-01")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        # Verify gone
        get_resp = client.get("/api/patients/PAT-DEL-01")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_patient_returns_404(self, client: TestClient) -> None:
        """DELETE /api/patients/{id} on nonexistent patient returns 404."""
        response = client.delete("/api/patients/NONEXISTENT")
        assert response.status_code == 404

    def test_negative_age_rejected(self, client: TestClient) -> None:
        """POST /api/patients with negative age is rejected with 422 Unprocessable Entity."""
        response = client.post("/api/patients", json={"age": -5})
        assert response.status_code == 422

    def test_empty_string_patient_id_rejected(self, client: TestClient) -> None:
        """POST /api/patients with empty whitespace patient_id is rejected."""
        response = client.post("/api/patients", json={"patient_id": "   "})
        assert response.status_code == 422

    def test_duplicate_patient_id_returns_400(self, client: TestClient) -> None:
        """POST /api/patients with duplicate patient_id returns 400 Bad Request."""
        client.post("/api/patients", json={"patient_id": "PAT-CLASH", "age": 20})
        response = client.post("/api/patients", json={"patient_id": "PAT-CLASH", "age": 21})
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
