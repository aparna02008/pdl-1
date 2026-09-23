import { useState } from 'react'
import PhotoDropzone from '../components/PhotoDropzone'
import VoiceRecorder from '../components/VoiceRecorder'
import LocationField from '../components/LocationField'
import { IconCheck, IconAlert } from '../components/Icons'
import { submitComplaint } from '../api/complaints'

export default function ReportIssue() {
  const [description, setDescription] = useState('')
  const [photos, setPhotos] = useState([])
  const [voiceClip, setVoiceClip] = useState(null)
  const [location, setLocation] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null) // { type: 'success' | 'error', message }

  const canSubmit = description.trim().length > 0 && !submitting

  async function handleSubmit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    setResult(null)
    try {
      await submitComplaint({ description, photos, voiceClip, location })
      setResult({ type: 'success', message: 'Reported. You can track its status under "My complaints".' })
      setDescription('')
      setPhotos([])
      setVoiceClip(null)
      setLocation(null)
    } catch (err) {
      setResult({
        type: 'error',
        message: `Couldn't reach the server — the report wasn't sent. ${err.message || ''}`.trim(),
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <h1>Report an issue</h1>
        <p>Potholes, speed breakers, or unpaved roads — describe what you see and where.</p>
      </div>

      {result && (
        <div className={`banner banner--${result.type}`}>
          {result.type === 'success' ? <IconCheck width={16} height={16} /> : <IconAlert width={16} height={16} />}
          <span>{result.message}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="report-grid">
          <div className="card card--fill">
            <div className="field">
              <label htmlFor="description">What's the issue?</label>
              <textarea
                id="description"
                rows={9}
                placeholder="E.g. Large pothole in the middle of the lane, gets flooded when it rains."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>

            <div className="field" style={{ marginBottom: 0 }}>
              <label>Photos</label>
              <PhotoDropzone files={photos} onChange={setPhotos} />
            </div>
          </div>

          <div className="card card--fill">
            <div className="field">
              <label>Voice note</label>
              <VoiceRecorder clip={voiceClip} onChange={setVoiceClip} />
            </div>

            <div className="field" style={{ marginBottom: 0 }}>
              <label>Location</label>
              <LocationField location={location} onChange={setLocation} />
            </div>
          </div>
        </div>

        <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
          <button type="submit" className="btn btn--primary" disabled={!canSubmit}>
            {submitting ? 'Submitting…' : 'Submit report'}
          </button>
        </div>
      </form>
    </div>
  )
}
