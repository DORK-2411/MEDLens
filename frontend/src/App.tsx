import React, { useState } from 'react'
import './App.css'

interface PatientRecord {
  patient_id: string
  age?: number | null
  sex?: string | null
  notes?: string | null
  symptoms: string[]
  conditions: string[]
  allergies: string[]
  medications: string[]
  reports?: unknown[]
  audit_log?: unknown[]
}

const API_BASE_URL = 'http://127.0.0.1:8000'

function App() {
  const [patientId, setPatientId] = useState('')
  const [age, setAge] = useState('')
  const [sex, setSex] = useState('')
  const [symptoms, setSymptoms] = useState('')
  const [conditions, setConditions] = useState('')
  const [allergies, setAllergies] = useState('')
  const [medications, setMedications] = useState('')
  const [notes, setNotes] = useState('')

  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [createdPatient, setCreatedPatient] = useState<PatientRecord | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setErrorMessage(null)

    const parseList = (val: string) =>
      val
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0)

    const payload: {
      patient_id?: string
      age?: number
      sex?: string
      notes?: string
      symptoms: string[]
      conditions: string[]
      allergies: string[]
      medications: string[]
    } = {
      symptoms: parseList(symptoms),
      conditions: parseList(conditions),
      allergies: parseList(allergies),
      medications: parseList(medications),
    }

    if (patientId.trim()) {
      payload.patient_id = patientId.trim()
    }
    if (age.trim() !== '') {
      const parsedAge = parseInt(age, 10)
      if (isNaN(parsedAge) || parsedAge < 0) {
        setErrorMessage('Age must be a non-negative number')
        setIsLoading(false)
        return
      }
      payload.age = parsedAge
    }
    if (sex.trim()) {
      payload.sex = sex.trim()
    }
    if (notes.trim()) {
      payload.notes = notes.trim()
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/patients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => null)
        const detail = errData?.detail || `Error ${response.status}: ${response.statusText}`
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
      }

      const data: PatientRecord = await response.json()
      setCreatedPatient(data)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message)
      } else {
        setErrorMessage('An unexpected error occurred while creating patient.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setPatientId('')
    setAge('')
    setSex('')
    setSymptoms('')
    setConditions('')
    setAllergies('')
    setMedications('')
    setNotes('')
    setCreatedPatient(null)
    setErrorMessage(null)
  }

  return (
    <div className="container">
      <header className="header">
        <h1>MEDLENS</h1>
        <p className="subtitle">AI-Powered Clinical Information Intelligence</p>
      </header>

      <main className="main-content">
        <section className="form-card">
          <h2>Create Patient Record</h2>

          {errorMessage && (
            <div className="alert alert-error">
              <strong>Error:</strong> {errorMessage}
            </div>
          )}

          {createdPatient && (
            <div className="alert alert-success">
              Patient record created successfully
            </div>
          )}

          <form onSubmit={handleSubmit} className="intake-form">
            <div className="form-group">
              <label htmlFor="patientId">Patient ID (optional):</label>
              <input
                id="patientId"
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="e.g. PAT-001 (auto-generated if empty)"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="age">Age:</label>
                <input
                  id="age"
                  type="number"
                  min="0"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  placeholder="e.g. 45"
                />
              </div>

              <div className="form-group">
                <label htmlFor="sex">Sex:</label>
                <select
                  id="sex"
                  value={sex}
                  onChange={(e) => setSex(e.target.value)}
                >
                  <option value="">Select sex</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="symptoms">Symptoms (comma-separated):</label>
              <input
                id="symptoms"
                type="text"
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                placeholder="e.g. Cough, Fever, Fatigue"
              />
            </div>

            <div className="form-group">
              <label htmlFor="conditions">Existing Conditions (comma-separated):</label>
              <input
                id="conditions"
                type="text"
                value={conditions}
                onChange={(e) => setConditions(e.target.value)}
                placeholder="e.g. Asthma, Hypertension"
              />
            </div>

            <div className="form-group">
              <label htmlFor="allergies">Allergies (comma-separated):</label>
              <input
                id="allergies"
                type="text"
                value={allergies}
                onChange={(e) => setAllergies(e.target.value)}
                placeholder="e.g. Penicillin, Peanuts"
              />
            </div>

            <div className="form-group">
              <label htmlFor="medications">Medications (comma-separated):</label>
              <input
                id="medications"
                type="text"
                value={medications}
                onChange={(e) => setMedications(e.target.value)}
                placeholder="e.g. Albuterol 90mcg, Metformin 500mg"
              />
            </div>

            <div className="form-group">
              <label htmlFor="notes">Notes:</label>
              <textarea
                id="notes"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Free-text clinical intake notes..."
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={isLoading}>
                {isLoading ? 'Creating...' : 'Create Patient'}
              </button>
              {createdPatient && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleReset}
                >
                  Create Another Patient
                </button>
              )}
            </div>
          </form>
        </section>

        {createdPatient && (
          <section className="record-card">
            <h3>Created Patient Information</h3>
            <div className="record-details">
              <p>
                <strong>Patient ID:</strong> <code>{createdPatient.patient_id}</code>
              </p>
              <p>
                <strong>Age:</strong> {createdPatient.age !== null && createdPatient.age !== undefined ? createdPatient.age : 'Not specified'}
              </p>
              <p>
                <strong>Sex:</strong> {createdPatient.sex || 'Not specified'}
              </p>
              <p>
                <strong>Symptoms:</strong>{' '}
                {createdPatient.symptoms.length > 0
                  ? createdPatient.symptoms.join(', ')
                  : 'None reported'}
              </p>
              <p>
                <strong>Conditions:</strong>{' '}
                {createdPatient.conditions.length > 0
                  ? createdPatient.conditions.join(', ')
                  : 'None reported'}
              </p>
              <p>
                <strong>Allergies:</strong>{' '}
                {createdPatient.allergies.length > 0
                  ? createdPatient.allergies.join(', ')
                  : 'No known allergies'}
              </p>
              <p>
                <strong>Medications:</strong>{' '}
                {createdPatient.medications.length > 0
                  ? createdPatient.medications.join(', ')
                  : 'No medications reported'}
              </p>
              {createdPatient.notes && (
                <p>
                  <strong>Notes:</strong> {createdPatient.notes}
                </p>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
