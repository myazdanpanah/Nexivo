import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LoginPage from './pages/LoginPage'
import DashboardListPage from './pages/DashboardListPage'
import DashboardBuilderPage from './pages/DashboardBuilderPage'
import DataUploadPage from './pages/DataUploadPage'
import AdminSettingsPage from './pages/AdminSettingsPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboards" replace />} />
      <Route path="/dashboards" element={<PrivateRoute><DashboardListPage /></PrivateRoute>} />
      <Route path="/dashboards/:id" element={<PrivateRoute><DashboardBuilderPage /></PrivateRoute>} />
      <Route path="/data/upload" element={<PrivateRoute><DataUploadPage /></PrivateRoute>} />
      <Route path="/admin/users" element={<PrivateRoute><AdminSettingsPage /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/dashboards" replace />} />
    </Routes>
  )
}
