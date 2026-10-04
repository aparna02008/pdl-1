const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Separate localStorage key from the citizen app on purpose — an admin and
// a citizen can be logged in at the same time in different tabs without
// clobbering each other's session.
const TOKEN_KEY = 'civiai_admin_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export async function adminLogin(email, password) {
  const res = await fetch(`${BASE_URL}/auth/admin-login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Login failed (${res.status})`)
  }
  return res.json() // { access_token, token_type }
}

export async function fetchMe() {
  const token = getToken()
  if (!token) throw new Error('Not logged in')
  const res = await fetch(`${BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Session expired')
  return res.json()
}
