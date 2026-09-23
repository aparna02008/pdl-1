import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import ReportIssue from './pages/ReportIssue'
import MyComplaints from './pages/MyComplaints'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Navigate to="/report" replace />} />
            <Route path="/report" element={<ReportIssue />} />
            <Route path="/complaints" element={<MyComplaints />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
