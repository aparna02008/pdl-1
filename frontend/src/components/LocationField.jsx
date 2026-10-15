import { useState } from 'react'
import { IconPin, IconCheck } from './Icons'

export default function LocationField({ location, onChange }) {
  const [status, setStatus] = useState('idle') // idle | locating | error
  const [manual, setManual] = useState(false)
  const [reason, setReason] = useState('')

  function fail(message) {
    setReason(message)
    setStatus('error')
    setManual(true)
  }

  function detect() {
    if (!navigator.geolocation) {
      fail("This device can't share its location")
      return
    }
    if (!window.isSecureContext) {
      fail('Location needs a secure (https) connection')
      return
    }
    setStatus('locating')
    setReason('')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onChange({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          address: '',
        })
        setStatus('idle')
      },
      (err) => {
        if (err.code === 1) fail('Location permission was denied')
        else if (err.code === 3) fail('Getting your location took too long')
        else fail('Your location is not available right now')
      },
      { enableHighAccuracy: true, timeout: 15000 }
    )
  }

  const hasFix = location?.lat != null && location?.lng != null

  return (
    <div>
      <div className="locate">
        <IconPin className="locate__icon" />
        <span className="locate__text">
          {hasFix
            ? `Location captured (${location.lat.toFixed(5)}, ${location.lng.toFixed(5)})`
            : status === 'locating'
              ? 'Getting your location…'
              : status === 'error'
                ? `${reason}. Enter a landmark or address below.`
                : 'Attach your current location'}
        </span>
        <button type="button" className="locate__action" onClick={detect} disabled={status === 'locating'}>
          {hasFix ? 'Update' : 'Use current location'}
        </button>
      </div>

      {hasFix && (
        <div className="map-frame" style={{ marginTop: 12 }}>
          {/* Real OpenStreetMap embed — no API key needed, no fabricated map */}
          <iframe
            title="Reported location"
            src={`https://www.openstreetmap.org/export/embed.html?bbox=${location.lng - 0.01}%2C${location.lat - 0.008}%2C${location.lng + 0.01}%2C${location.lat + 0.008}&layer=mapnik&marker=${location.lat}%2C${location.lng}`}
            loading="lazy"
          />
        </div>
      )}

      {!hasFix && (
        <div className="map-placeholder" style={{ marginTop: 12 }}>
          <IconPin width={22} height={22} />
          <span>The map preview appears here once a location is attached</span>
        </div>
      )}

      {(manual || location?.address !== undefined) && (
        <div className="field" style={{ marginTop: 10, marginBottom: 0 }}>
          <input
            type="text"
            placeholder="Or type a landmark or address"
            value={location?.address || ''}
            onChange={(e) => onChange({ ...(location || {}), address: e.target.value })}
          />
        </div>
      )}

      {hasFix && (
        <div className="banner banner--success" style={{ marginTop: 12, marginBottom: 0 }}>
          <IconCheck width={16} height={16} />
          <span>Location added to this report.</span>
        </div>
      )}
    </div>
  )
}
