import { useState } from 'react'
import PhotoDropzone from '../components/PhotoDropzone'
import VoiceRecorder from '../components/VoiceRecorder'
import LocationField from '../components/LocationField'
import Toast from '../components/Toast'
import { IconCheck, IconAlert, IconShield } from '../components/Icons'
import { submitComplaint } from '../api/complaints'

const DESCRIPTION_MAX = 500

const CATEGORIES = [
  { value: '', label: 'Select a category' },
  { value: 'pothole', label: 'Pothole' },
  { value: 'speed_breaker', label: 'Speed breaker' },
  { value: 'unpaved_road', label: 'Unpaved / damaged road' },
  { value: 'garbage', label: 'Garbage / waste' },
  { value: 'waterlogging', label: 'Waterlogging' },
  { value: 'open_manhole', label: 'Open manhole' },
  { value: 'damaged_road_sign', label: 'Damaged road sign' },
  { value: 'illegal_parking', label: 'Illegal parking' },
]

const SEVERITIES = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

export default function ReportIssue() {
  const [category, setCategory] = useState('')
  const [severity, setSeverity] = useState('medium')
  const [description, setDescription] = useState('')
  const [photos, setPhotos] = useState([])
  const [voiceClip, setVoiceClip] = useState(null)
  const [location, setLocation] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [justSucceeded, setJustSucceeded] = useState(false)
  const [banner, setBanner] = useState(null)
  const [toast, setToast] = useState(null)

  const detailsDone = description.trim().length > 0
  const locationDone = !!location?.lat || !!location?.address
  const canSubmit = detailsDone && !submitting

  async function handleSubmit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    setBanner(null)
    try {
      await submitComplaint({
        description,
        photos,
        voiceClip,
        location,
        reportedCategory: category || null,
        reportedSeverity: severity,
      })
      setJustSucceeded(true)
      setToast({ type: 'success', message: 'Reported. Track it under "My complaints".' })
      setCategory('')
      setSeverity('medium')
      setDescription('')
      setPhotos([])
      setVoiceClip(null)
      setLocation(null)
      setTimeout(() => setJustSucceeded(false), 1400)
    } catch (err) {
      setBanner({
        type: 'error',
        message: `Couldn't reach the server — the report wasn't sent. ${err.message || ''}`.trim(),
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-content">
      <Toast toast={toast} onDismiss={() => setToast(null)} />

      <div className="page-header page-header--with-stepper">
        <div>
          <h1>Report an issue</h1>
          <p>Help us make your city cleaner, safer and better. Share what you see and where it is.</p>
        </div>

        <div className="stepper" aria-hidden="true">
          <Step n={1} label="Details" state={detailsDone ? 'done' : 'current'} />
          <span className="stepper__line" />
          <Step n={2} label="Location" state={locationDone ? 'done' : detailsDone ? 'current' : 'upcoming'} />
          <span className="stepper__line" />
          <Step n={3} label="Review" state="upcoming" />
          <span className="stepper__line" />
          <Step n={4} label="Submit" state={justSucceeded ? 'done' : 'upcoming'} />
        </div>
      </div>

      {banner && (
        <div className={`banner banner--${banner.type}`}>
          <IconAlert width={16} height={16} />
          <span>{banner.message}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="report-grid">
          <div className="card card--fill">
            <div className="section-head">
              <span className="section-head__title">
                <span className="section-head__badge">1</span>
                Issue details
              </span>
              <span className="section-head__required">Required</span>
            </div>

            <div className="field" style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 14 }}>
              <div>
                <label htmlFor="category">Issue category</label>
                <div className="select-wrap">
                  <select id="category" value={category} onChange={(e) => setCategory(e.target.value)}>
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
                <div className="field__hint">Select the type of issue you're reporting.</div>
              </div>
              <div>
                <label>Severity</label>
                <div className="severity-group">
                  {SEVERITIES.map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      className={'severity-pill' + (severity === s.value ? ` is-selected--${s.value}` : '')}
                      onClick={() => setSeverity(s.value)}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
                <div className="field__hint">Helps us prioritise urgent issues.</div>
              </div>
            </div>

            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                rows={6}
                maxLength={DESCRIPTION_MAX}
                placeholder="Describe the issue in detail. Include landmarks, nearby buildings, or anything else that can help us understand it better."
                value={description}
                onChange={(e) => setDescription(e.target.value.slice(0, DESCRIPTION_MAX))}
                required
              />
              <div className="char-count">{description.length}/{DESCRIPTION_MAX}</div>
              <div className="field__hint">Be clear and specific for faster resolution.</div>
            </div>
          </div>

          <div className="card card--fill">
            <div className="section-head">
              <span className="section-head__title">
                <span className="section-head__badge">4</span>
                Location
              </span>
              <span className="section-head__required">Required</span>
            </div>
            <p className="field__hint" style={{ marginTop: -8, marginBottom: 14 }}>
              Find your current location, or add a landmark below.
            </p>
            <LocationField location={location} onChange={setLocation} />

            <div className="banner banner--info" style={{ marginTop: 14, marginBottom: 0 }}>
              <IconShield width={16} height={16} />
              <span>
                <span className="banner__title">Your report matters</span>
                We'll review your submission and keep you updated on the progress.
              </span>
            </div>
          </div>
        </div>

        <div className="card" style={{ marginTop: 16 }}>
          <div className="section-head">
            <span className="section-head__title">
              <span className="section-head__badge">2</span>
              Photos
            </span>
            <span className="section-head__optional">Optional</span>
          </div>
          <PhotoDropzone files={photos} onChange={setPhotos} />
        </div>

        <div className="card" style={{ marginTop: 16 }}>
          <div className="section-head">
            <span className="section-head__title">
              <span className="section-head__badge">3</span>
              Voice note
            </span>
            <span className="section-head__optional">Optional</span>
          </div>
          <VoiceRecorder clip={voiceClip} onChange={setVoiceClip} />
        </div>

        <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
          <button
            type="submit"
            className={'btn btn--primary' + (justSucceeded ? ' btn--success' : '')}
            disabled={!canSubmit}
            style={{ minWidth: 180 }}
          >
            {justSucceeded ? (
              <>
                <span className="btn__check"><IconCheck width={16} height={16} /></span>
                Reported
              </>
            ) : submitting ? 'Submitting…' : 'Submit report'}
          </button>
        </div>
      </form>
    </div>
  )
}

function Step({ n, label, state }) {
  return (
    <span className={'stepper__step' + (state === 'done' ? ' is-done' : state === 'current' ? ' is-current' : '')}>
      <span className="stepper__circle">{state === 'done' ? <IconCheck width={12} height={12} /> : n}</span>
      <span className="stepper__label">{label}</span>
    </span>
  )
}
