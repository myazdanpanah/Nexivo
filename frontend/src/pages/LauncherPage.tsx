import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useToast } from '../components/Toast'
import api from '../api/client'
import {
  BarChart3, DollarSign, Users, Database, Upload,
  Settings, ArrowLeft, LogOut, Zap
} from 'lucide-react'

interface ModuleInfo {
  id: string
  label: string
}

const MODULE_ICONS: Record<string, React.ElementType> = {
  bi_dashboard: BarChart3,
  finance: DollarSign,
  crm: Users,
  db_manager: Database,
  datasets: Upload,
  settings: Settings,
}

const MODULE_COLORS: Record<string, string> = {
  bi_dashboard: 'from-indigo-500 to-purple-600',
  finance: 'from-emerald-500 to-teal-600',
  crm: 'from-blue-500 to-cyan-600',
  db_manager: 'from-orange-500 to-amber-600',
  datasets: 'from-pink-500 to-rose-600',
  settings: 'from-gray-500 to-slate-600',
}

const MODULE_ROUTES: Record<string, string> = {
  bi_dashboard: '/dashboards',
  finance: '/finance',
  crm: '/crm',
  db_manager: '/db-manager',
  datasets: '/data/upload',
  settings: '/settings',
}

const MODULE_DESCRIPTIONS: Record<string, string> = {
  bi_dashboard: 'داشبوردها و نمودارهای هوشمند',
  finance: 'صورتحساب، پرداخت‌ها و مدیریت مالی',
  crm: 'مدیریت ارتباط با مشتریان',
  db_manager: 'مدیریت پایگاه داده و جداول',
  datasets: 'آپلود و مدیریت داده‌ها',
  settings: 'تنظیمات سازمان و ماژول‌ها',
}

export default function LauncherPage() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [modules, setModules] = useState<ModuleInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchModules()
  }, [])

  const fetchModules = async () => {
    try {
      const res = await api.get('/auth/user-modules/')
      setModules(res.data)
    } catch {
      toast('خطا در دریافت ماژول‌ها', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleModuleClick = (moduleId: string) => {
    const route = MODULE_ROUTES[moduleId]
    if (route) {
      navigate(route)
    } else {
      toast(`ماژول ${moduleId} هنوز فعال نیست`, 'error')
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-700/50 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Nexivo</h1>
              <p className="text-xs text-gray-400">سازمان هوشمند</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-left">
              <p className="text-sm font-medium text-white">
                {user?.first_name || user?.last_name
                  ? `${user.first_name} ${user.last_name}`
                  : user?.username}
              </p>
              <p className="text-xs text-gray-400">{user?.company_name || 'بدون شرکت'}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-xl transition"
              title="خروج"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="max-w-4xl w-full">
          {/* Welcome */}
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">
              خوش آمدید، {user?.first_name || user?.username}
            </h2>
            <p className="text-gray-400 text-lg">
              ماژول مورد نظر خود را انتخاب کنید
            </p>
          </div>

          {/* Module Grid */}
          {loading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-gray-400 mt-4">در حال بارگذاری ماژول‌ها...</p>
            </div>
          ) : modules.length === 0 ? (
            <div className="text-center py-12">
              <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 text-lg">هیچ ماژولی فعال نیست</p>
              <p className="text-gray-500 text-sm mt-2">
                با مدیر سیستم تماس بگیرید تا ماژول‌ها را فعال کند
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {modules.map((mod) => {
                const Icon = MODULE_ICONS[mod.id] || Database
                const gradient = MODULE_COLORS[mod.id] || 'from-gray-500 to-gray-600'
                const description = MODULE_DESCRIPTIONS[mod.id] || ''
                return (
                  <button
                    key={mod.id}
                    onClick={() => handleModuleClick(mod.id)}
                    className="group relative overflow-hidden bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 text-right hover:border-indigo-500/50 hover:bg-gray-800/80 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl hover:shadow-indigo-500/10"
                  >
                    {/* Gradient overlay on hover */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
                    
                    <div className="relative">
                      <div className={`w-12 h-12 bg-gradient-to-br ${gradient} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-bold text-white mb-1">{mod.label}</h3>
                      {description && (
                        <p className="text-sm text-gray-400">{description}</p>
                      )}
                      <div className="mt-4 flex items-center gap-1 text-indigo-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                        <span>ورود</span>
                        <ArrowLeft className="w-4 h-4" />
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700/50 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-500">
          <span>Nexivo v0.1.0</span>
          <span>پلتفرم سازمان هوشمند</span>
        </div>
      </footer>
    </div>
  )
}
