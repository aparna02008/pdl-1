import { useState } from 'react'
import { IconPin } from './Icons'

export default function LocationField({ location, onChange }) {
  const [status, setStatus] = useState('idle') // idle | locating | error
  const [manual, setManual] = useState(false)

  function detect() {
    if (!navigator.geolocation) {
      setStatus('error')
      setManual(true)
      return
    }
    setStatus('locating')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onChange({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          address: '',
        })
        setStatus('idle')
      },
      () => {
        setStatus('error')
        setManual(true)
      },
      { enableHighAccuracy: true, timeout: 8000 }
    )
  }

  return (
    <div>
      <div className="locate">
        <IconPin className="locate__icon" />
        <span className="locate__text">
          {location?.lat
            ? `Location captured (${location.lat.toFixed(5)}, ${location.lng.toFixed(5)})`
            : status === 'locating'
              ? 'Getting your location…'
              : status === 'error'
                ? "Couldn't get your location automatically — enter it below"
                : 'Attach your current location'}
        </span>
        <button type="button" className="locate__action" onClick={detect} disabled={status === 'locating'}>
          {location?.lat ? 'Update' : 'Use current location'}
        </button>
      </div>

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
    </div>
  )
}
