import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then(response => {
        if (response.ok) {
          return response.json()
        }
        throw new Error('Network response was not ok.')
      })
      .then(data => {
        setApiStatus(`Connected: ${data.status} (${data.service})`)
      })
      .catch(error => {
        setApiStatus(`Error: ${error.message}`)
      })
  }, [])

  return (
    <div className="App">
      <h1>MedLens</h1>
      <p>AI-Powered Clinical Information Intelligence</p>
      
      <div className="card">
        <h2>Backend API Status</h2>
        <p>{apiStatus}</p>
      </div>
    </div>
  )
}

export default App
