import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'
import { Plus, BarChart3, Upload, LogOut, ChevronLeft } from 'lucide-react'

interface Dashboard {
  id: number
  name: string
  description: string
  owner_name: string
  is_published: boolean
  widgets: unknown[]
  created_at: string
}

export default function DashboardListPage() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([])
  const [loading, setLoading] = useState(true)
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchDashboards()
  }, [])

  const fetchDashboards = async () => {
    try {
      const res = await api.get('/dashboards/')
      setDashboards(res.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const createDashboard = async () => {
    try {
      const res = await api.post('/dashboards/', {
        name: 'داشبورد جدید',
        description: '',
        allowed_roles: ['ceo', 'finance', 'sales'],
      })
      navigate(`/dashboards/${res.data.id}`)
    } catch {
      // ignore
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const roleLabels: Record<string, string> = {
    ceo: 'مدیرعامل',
    finance: 'مالی',
    sales: 'فروش',
    admin: 'مدیر سیستم',
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">نکسیوو</h1>
              <p className="text-xs text-gray-500">پلتفرم داشبورد هوشمند</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/data/upload"
              className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-xl transition"
            >
              <Upload className="w-4 h-4" />
              بارگذاری داده
            </Link>

            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="font-medium">{user?.username}</span>
              <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-lg text-xs font-medium">
                {roleLabels[user?.role || ''] || user?.role}
              </span>
            </div>

            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-red-500 transition"
              title="خروج"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold text-gray-900">داشبوردها</h2>
          <button
            onClick={createDashboard}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            داشبورد جدید
          </button>
        </div>

        {loading ? (
          <div className="text-center py-20 text-gray-500">در حال بارگذاری...</div>
        ) : dashboards.length === 0 ? (
          <div className="text-center py-20">
            <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">هنوز داشبوردی ندارید</h3>
            <p className="text-gray-500 mb-6">اولین داشبورد خود را بسازید</p>
            <button
              onClick={createDashboard}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition font-medium"
            >
              ساخت داشبورد
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dashboards.map((d) => (
              <Link
                key={d.id}
                to={`/dashboards/${d.id}`}
                className="group bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg hover:border-indigo-300 transition"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-bold text-gray-900 group-hover:text-indigo-600 transition">
                    {d.name}
                  </h3>
                  <ChevronLeft className="w-5 h-5 text-gray-400 group-hover:text-indigo-500 transition" />
                </div>
                <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                  {d.description || 'بدون توضیح'}
                </p>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{d.widgets?.length || 0} نمودار</span>
                  <span>{d.owner_name}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
