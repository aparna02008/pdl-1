import { useAdminAuth } from './AdminAuthContext'
import AdminLogin from '../pages/Login'

export default function ProtectedRoute({ children }) {
  const { token, loading } = useAdminAuth()

  if (loading) {
    return <div className="admin-auth-loading">Loading…</div>
  }

  if (!token) {
    return <AdminLogin />
  }

  return children
}
