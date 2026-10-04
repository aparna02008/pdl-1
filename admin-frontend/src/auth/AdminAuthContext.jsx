import { createContext, useContext, useEffect, useState } from 'react'
import { adminLogin, fetchMe, getToken, setToken, clearToken } from '../api/auth'

const AdminAuthContext = createContext(null)

export function AdminAuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setTok] = useState(getToken())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    fetchMe()
      .then(setUser)
      .catch(() => {
        clearToken()
        setTok(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  async function login(email, password) {
    const data = await adminLogin(email, password)
    setToken(data.access_token)
    setTok(data.access_token)
    const me = await fetchMe()
    setUser(me)
    return me
  }

  function logout() {
    clearToken()
    setTok(null)
    setUser(null)
  }

  return (
    <AdminAuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AdminAuthContext.Provider>
  )
}

export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext)
  if (!ctx) throw new Error('useAdminAuth must be used inside AdminAuthProvider')
  return ctx
}
