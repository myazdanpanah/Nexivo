import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import LoginPage from './pages/LoginPage'
import LauncherPage from './pages/LauncherPage'
import SettingsPage from './pages/SettingsPage'
import DashboardListPage from './pages/DashboardListPage'
import DashboardBuilderPage from './pages/DashboardBuilderPage'
import DataUploadPage from './pages/DataUploadPage'
import AdminSettingsPage from './pages/AdminSettingsPage'
import DashboardAssignPage from './pages/DashboardAssignPage'
import OrgChartPage from './pages/OrgChartPage'
import DatabaseManagerPage from './pages/DatabaseManagerPage'
import TableEditorPage from './pages/TableEditorPage'
import SchemaEditorPage from './pages/SchemaEditorPage'
import SqlEditorPage from './pages/SqlEditorPage'
import FileImportPage from './pages/FileImportPage'
import ExternalDbPage from './pages/ExternalDbPage'
import SheetsSyncPage from './pages/SheetsSyncPage'
import SupersetHealthPage from './pages/SupersetHealthPage'
import LLMSettingsPage from './pages/LLMSettingsPage'
import RoadmapPage from './pages/RoadmapPage'
// Finance module
import FinanceLayout from './pages/finance/FinanceLayout'
import FinanceDashboard from './pages/finance/FinanceDashboard'
import ChartOfAccountsPage from './pages/finance/ChartOfAccountsPage'
import InvoicesPage from './pages/finance/InvoicesPage'
import ReceiptsPage from './pages/finance/ReceiptsPage'
import PaymentsPage from './pages/finance/PaymentsPage'
import ChequesPage from './pages/finance/ChequesPage'
import CustomersPage from './pages/finance/CustomersPage'
import SuppliersPage from './pages/finance/SuppliersPage'
import VouchersPage from './pages/finance/VouchersPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {/* Launcher — the splash page after login */}
      <Route path="/launcher" element={<PrivateRoute><LauncherPage /></PrivateRoute>} />
      <Route path="/" element={<PrivateRoute><LauncherPage /></PrivateRoute>} />
      {/* Settings — standalone page for module & org management */}
      <Route path="/settings" element={<PrivateRoute><SettingsPage /></PrivateRoute>} />
      <Route path="/settings/:tab" element={<PrivateRoute><SettingsPage /></PrivateRoute>} />
      {/* LLM Settings — system-level AI configuration */}
      <Route path="/settings/ai" element={<PrivateRoute><LLMSettingsPage /></PrivateRoute>} />
      {/* BI Dashboard module */}
      <Route path="/dashboards" element={<PrivateRoute><DashboardListPage /></PrivateRoute>} />
      <Route path="/dashboards/:id" element={<PrivateRoute><DashboardBuilderPage /></PrivateRoute>} />
      <Route path="/data/upload" element={<PrivateRoute><DataUploadPage /></PrivateRoute>} />
      <Route path="/admin/users" element={<PrivateRoute><AdminSettingsPage /></PrivateRoute>} />
      <Route path="/admin/assignments" element={<PrivateRoute><DashboardAssignPage /></PrivateRoute>} />
      <Route path="/org-chart" element={<PrivateRoute><OrgChartPage /></PrivateRoute>} />
      {/* Database Manager module */}
      <Route path="/db-manager" element={<PrivateRoute><DatabaseManagerPage /></PrivateRoute>} />
      <Route path="/db-manager/table/:source/:table" element={<PrivateRoute><TableEditorPage /></PrivateRoute>} />
      <Route path="/db-manager/table/:source/:table/schema" element={<PrivateRoute><SchemaEditorPage /></PrivateRoute>} />
      <Route path="/db-manager/table/:source/:table/import" element={<PrivateRoute><FileImportPage /></PrivateRoute>} />
      <Route path="/db-manager/sql" element={<PrivateRoute><SqlEditorPage /></PrivateRoute>} />
      <Route path="/db-manager/syncs" element={<PrivateRoute><SheetsSyncPage /></PrivateRoute>} />
      <Route path="/db-manager/connections" element={<PrivateRoute><ExternalDbPage /></PrivateRoute>} />
      <Route path="/admin/superset" element={<PrivateRoute><SupersetHealthPage /></PrivateRoute>} />
      {/* Finance module */}
      <Route path="/finance" element={<PrivateRoute><FinanceLayout /></PrivateRoute>}>
        <Route index element={<FinanceDashboard />} />
        <Route path="chart-of-accounts" element={<ChartOfAccountsPage />} />
        <Route path="invoices" element={<InvoicesPage />} />
        <Route path="receipts" element={<ReceiptsPage />} />
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="cheques" element={<ChequesPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="suppliers" element={<SuppliersPage />} />
        <Route path="vouchers" element={<VouchersPage />} />
      </Route>
      {/* Roadmap */}
      <Route path="/roadmap" element={<PrivateRoute><RoadmapPage /></PrivateRoute>} />
      {/* Fallback → launcher */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
