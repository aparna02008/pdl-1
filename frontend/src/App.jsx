import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import ReportIssue from './pages/ReportIssue'
import MyComplaints from './pages/MyComplaints'
import Login from './pages/Login'
import Signup from './pages/Signup'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'

function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-shell__content">
        <Topbar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Navigate to="/report" replace />} />
            <Route path="/report" element={<ReportIssue />} />
            <Route path="/complaints" element={<MyComplaints />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
