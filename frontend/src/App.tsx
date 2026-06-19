import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LoginPage from './pages/LoginPage'
import DashboardListPage from './pages/DashboardListPage'
import DashboardBuilderPage from './pages/DashboardBuilderPage'
import DataUploadPage from './pages/DataUploadPage'

function App() {
  const { token } = useAuthStore()

  if (!token) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboards" replace />} />
      <Route path="/login" element={<Navigate to="/dashboards" replace />} />
      <Route path="/dashboards" element={<DashboardListPage />} />
      <Route path="/dashboards/:id" element={<DashboardBuilderPage />} />
      <Route path="/data/upload" element={<DataUploadPage />} />
      <Route path="*" element={<Navigate to="/dashboards" replace />} />
    </Routes>
  )
}

export default App
