const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function submitComplaint({ description, photos, voiceClip, location }) {
  const form = new FormData()
  form.append('description', description)
  if (location?.lat) form.append('lat', location.lat)
  if (location?.lng) form.append('lng', location.lng)
  if (location?.address) form.append('address', location.address)
  photos.forEach((file) => form.append('photos', file))
  if (voiceClip) form.append('voice_note', voiceClip, 'voice-note.webm')

  const res = await fetch(`${BASE_URL}/complaints`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Server responded with ${res.status}`)
  }
  return res.json()
}

export async function fetchComplaints() {
  const res = await fetch(`${BASE_URL}/complaints`)
  if (!res.ok) {
    throw new Error(`Server responded with ${res.status}`)
  }
  return res.json()
}
