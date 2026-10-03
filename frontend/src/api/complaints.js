const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function authHeaders() {
  const token = localStorage.getItem('civisense_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function submitComplaint({ description, photos, voiceClip, location, reportedCategory, reportedSeverity }) {
  const form = new FormData()
  form.append('description', description)
  if (location?.lat != null) form.append('lat', location.lat)
  if (location?.lng != null) form.append('lng', location.lng)
  if (location?.address) form.append('address', location.address)
  if (reportedCategory) form.append('reported_category', reportedCategory)
  if (reportedSeverity) form.append('reported_severity', reportedSeverity)
  photos.forEach((file) => form.append('photos', file))
  if (voiceClip) form.append('voice_note', voiceClip, 'voice-note.webm')

  const res = await fetch(`${BASE_URL}/complaints`, {
    method: 'POST',
    headers: { ...authHeaders() },
    body: form,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Server responded with ${res.status}`)
  }
  return res.json()
}

export async function fetchMyComplaints() {
  const res = await fetch(`${BASE_URL}/complaints/mine`, {
    headers: { ...authHeaders() },
  })
  if (!res.ok) {
    throw new Error(`Server responded with ${res.status}`)
  }
  return res.json()
}

export async function fetchComplaints(filters = {}) {
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.issue_type) params.set('issue_type', filters.issue_type)
  const qs = params.toString()
  const res = await fetch(`${BASE_URL}/complaints${qs ? `?${qs}` : ''}`)
  if (!res.ok) {
    throw new Error(`Server responded with ${res.status}`)
  }
  return res.json()
}

export async function updateComplaintStatus(id, status) {
  const res = await fetch(`${BASE_URL}/complaints/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Server responded with ${res.status}`)
  }
  return res.json()
}

export async function fetchStatsSummary() {
  const res = await fetch(`${BASE_URL}/complaints/stats/summary`)
  if (!res.ok) {
    throw new Error(`Server responded with ${res.status}`)
  }
  return res.json()
}
