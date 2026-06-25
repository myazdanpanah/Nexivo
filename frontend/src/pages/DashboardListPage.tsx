import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { Plus, BarChart3, Upload, LogOut, ChevronLeft, LayoutTemplate, TrendingUp, DollarSign, Megaphone, Users, ShoppingBag, Trash2, Copy, Share2, Shield, MoreVertical, X, UserCheck, FolderTree } from 'lucide-react'
import { ALL_ROLES } from '../utils/roles'

interface Dashboard {
  id: number
  name: string
  description: string
  owner_name: string
  is_published: boolean
  allowed_roles: string[]
  widgets: unknown[]
  pages?: Array<{ id: number; name: string; widgets: unknown[] }>
  created_at: string
  assignment_id?: number
  assigned_by_name?: string
  assignment_data_filters?: unknown[]
}

interface Template {
  id: string
  name: string
  description: string
  page_count: number
  widget_count: number
}

const TEMPLATE_ICONS: Record<string, typeof BarChart3> = {
  sales: TrendingUp,
  finance: DollarSign,
  marketing: Megaphone,
  hr: Users,
  retail: ShoppingBag,
  blank: BarChart3,
}

const TEMPLATE_COLORS: Record<string, string> = {
  sales: 'bg-emerald-500',
  finance: 'bg-blue-500',
  marketing: 'bg-pink-500',
  hr: 'bg-purple-500',
  retail: 'bg-orange-500',
  blank: 'bg-gray-400',
}



export default function DashboardListPage() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([])
  const [loading, setLoading] = useState(true)
  const [showTemplates, setShowTemplates] = useState(false)
  const [templates, setTemplates] = useState<Template[]>([])
  const [creatingFromTemplate, setCreatingFromTemplate] = useState<string | null>(null)
  const [activeMenu, setActiveMenu] = useState<number | null>(null)
  const [shareModal, setShareModal] = useState<Dashboard | null>(null)
  const [shareRoles, setShareRoles] = useState<string[]>([])
  const [assignedDashboards, setAssignedDashboards] = useState<Set<number>>(new Set())
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToast()
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchDashboards()
    fetchTemplates()
    fetchAssignedDashboards()
  }, [])

  // Close menus on outside click
  useEffect(() => {
    if (!activeMenu) return
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setActiveMenu(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [activeMenu])

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

  const fetchTemplates = async () => {
    try {
      const res = await api.get('/dashboards/templates/')
      setTemplates(res.data)
    } catch {
      // ignore
    }
  }

  const fetchAssignedDashboards = async () => {
    try {
      const res = await api.get('/dashboards/my-assigned/')
      const ids = new Set<number>(res.data.map((d: { id: number }) => d.id))
      setAssignedDashboards(ids)
    } catch {
      // ignore
    }
  }

  const createDashboard = async () => {
    try {
      const res = await api.post('/dashboards/', {
        name: 'داشبورد جدید',
        description: '',
        allowed_roles: ['ceo', 'finance', 'sales', 'admin'],
      })
      toast('داشبورد جدید ساخته شد', 'success')
      navigate(`/dashboards/${res.data.id}`)
    } catch {
      toast('خطا در ساخت داشبورد', 'error')
    }
  }

  const createFromTemplate = async (templateId: string) => {
    const tmpl = templates.find((t) => t.id === templateId)
    const name = tmpl?.name || templateId
    if (!window.confirm(`آیا از ساخت داشبورد «${name}» از قالب اطمینان دارید؟`)) return
    setCreatingFromTemplate(templateId)
    try {
      const res = await api.post('/dashboards/create-from-template/', {
        template_id: templateId,
      })
      toast('داشبورد از قالب ساخته شد', 'success')
      setShowTemplates(false)
      navigate(`/dashboards/${res.data.id}`)
    } catch {
      toast('خطا در ساخت داشبورد از قالب', 'error')
    } finally {
      setCreatingFromTemplate(null)
    }
  }

  const handleDeleteDashboard = async (d: Dashboard) => {
    if (!window.confirm(`آیا از حذف داشبورد «${d.name}» اطمینان دارید؟ این عمل غیرقابل بازگشت است.`)) return
    try {
      await api.delete(`/dashboards/${d.id}/`)
      setDashboards((prev) => prev.filter((x) => x.id !== d.id))
      toast('داشبورد حذف شد', 'success')
    } catch {
      toast('خطا در حذف داشبورد', 'error')
    }
    setActiveMenu(null)
  }

  const handleDuplicateDashboard = async (d: Dashboard) => {
    try {
      await api.post(`/dashboards/${d.id}/duplicate/`)
      toast('داشبورد کپی شد', 'success')
      fetchDashboards()
      setActiveMenu(null)
    } catch {
      toast('خطا در کپی داشبورد', 'error')
    }
  }

  const openShareModal = (d: Dashboard) => {
    setShareRoles(d.allowed_roles || [])
    setShareModal(d)
    setActiveMenu(null)
  }

  const handleShareSave = async () => {
    if (!shareModal) return
    try {
      await api.put(`/dashboards/${shareModal.id}/share/`, {
        allowed_roles: shareRoles,
      })
      setDashboards((prev) =>
        prev.map((d) =>
          d.id === shareModal.id ? { ...d, allowed_roles: shareRoles } : d
        )
      )
      setShareModal(null)
      toast('دسترسی‌ها به‌روز شد', 'success')
    } catch {
      toast('خطا در به‌روزرسانی دسترسی‌ها', 'error')
    }
  }

  const toggleShareRole = (role: string) => {
    setShareRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    )
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

  const canManage = user?.role === 'admin' || user?.role === 'ceo'

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

            {canManage && (
              <Link
                to="/admin/org"
                className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl transition"
              >
                <FolderTree className="w-4 h-4" />
                ساختار سازمانی
              </Link>
            )}

            {canManage && (
              <Link
                to="/admin/assignments"
                className="flex items-center gap-2 px-4 py-2 text-sm bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-xl transition"
              >
                <UserCheck className="w-4 h-4" />
                تخصیص داشبورد
              </Link>
            )}

            {canManage && (
              <Link
                to="/admin/users"
                className="flex items-center gap-2 px-4 py-2 text-sm bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 rounded-xl transition"
              >
                <Shield className="w-4 h-4" />
                مدیریت کاربران
              </Link>
            )}

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
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition text-sm font-medium"
            >
              <LayoutTemplate className="w-4 h-4" />
              استفاده از قالب
            </button>
            <button
              onClick={createDashboard}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              داشبورد جدید
            </button>
          </div>
        </div>

        {/* Template Picker */}
        {showTemplates && (
          <div className="mb-8 bg-white rounded-2xl border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">قالب‌های آماده</h3>
            <p className="text-sm text-gray-500 mb-6">یک قالب انتخاب کنید تا داشبورد شما با نمودارهای پیش‌فرض ساخته شود. سپس می‌توانید داده‌ها و تنظیمات را تغییر دهید.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((tmpl) => {
                const Icon = TEMPLATE_ICONS[tmpl.id] || BarChart3
                const colorClass = TEMPLATE_COLORS[tmpl.id] || 'bg-gray-400'
                const isCreating = creatingFromTemplate === tmpl.id
                return (
                  <button
                    key={tmpl.id}
                    onClick={() => createFromTemplate(tmpl.id)}
                    disabled={isCreating}
                    className="text-right p-4 border border-gray-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition group disabled:opacity-50"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-10 h-10 ${colorClass} rounded-lg flex items-center justify-center flex-shrink-0`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-bold text-gray-900 group-hover:text-indigo-600 transition text-sm">
                          {isCreating ? 'در حال ساخت...' : tmpl.name}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">{tmpl.description}</p>
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                          <span>{tmpl.page_count} صفحه</span>
                          <span>{tmpl.widget_count} نمودار</span>
                        </div>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center py-20 text-gray-500">در حال بارگذاری...</div>
        ) : dashboards.length === 0 ? (
          <div className="text-center py-20">
            <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">هنوز داشبوردی ندارید</h3>
            <p className="text-gray-500 mb-6">اولین داشبورد خود را بسازید یا از یک قالب شروع کنید</p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => setShowTemplates(true)}
                className="px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition font-medium"
              >
                <LayoutTemplate className="w-4 h-4 inline ml-2" />
                استفاده از قالب
              </button>
              <button
                onClick={createDashboard}
                className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition font-medium"
              >
                ساخت داشبورد
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dashboards.map((d) => (
              <div
                key={d.id}
                className="group bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-lg hover:border-indigo-300 transition relative"
              >
                <Link to={`/dashboards/${d.id}`} className="block">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-bold text-gray-900 group-hover:text-indigo-600 transition">
                      {d.name}
                    </h3>
                    <ChevronLeft className="w-5 h-5 text-gray-400 group-hover:text-indigo-500 transition" />
                  </div>
                  <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                    {d.description || 'بدون توضیح'}
                  </p>
                </Link>

                {/* Action buttons */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    {assignedDashboards.has(d.id) && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded text-[10px] font-medium">
                        <UserCheck className="w-2.5 h-2.5" />
                        تخصیص
                      </span>
                    )}
                    <span>{d.pages && d.pages.length > 0 ? `${d.pages.length} صفحه` : `${d.widgets?.length || 0} نمودار`}</span>
                    <span className="mx-1">·</span>
                    <span>{d.owner_name}</span>
                  </div>

                  {/* Three-dot menu */}
                  <div className="relative" ref={activeMenu === d.id ? menuRef : undefined}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setActiveMenu(activeMenu === d.id ? null : d.id)
                      }}
                      className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition opacity-0 group-hover:opacity-100"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>

                    {activeMenu === d.id && (
                      <div className="absolute bottom-full left-0 mb-1 bg-white border border-gray-200 rounded-xl shadow-lg py-1 z-50 min-w-[160px]">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDuplicateDashboard(d)
                          }}
                          className="flex items-center gap-2 w-full px-3 py-2 text-xs text-gray-700 hover:bg-gray-50"
                        >
                          <Copy className="w-3.5 h-3.5" />
                          کپی داشبورد
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            openShareModal(d)
                          }}
                          className="flex items-center gap-2 w-full px-3 py-2 text-xs text-gray-700 hover:bg-gray-50"
                        >
                          <Share2 className="w-3.5 h-3.5" />
                          اشتراک‌گذاری
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteDashboard(d)
                          }}
                          className="flex items-center gap-2 w-full px-3 py-2 text-xs text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          حذف داشبورد
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Share Modal */}
      {shareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" dir="rtl">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShareModal(null)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h3 className="font-bold text-gray-900">اشتراک‌گذاری: {shareModal.name}</h3>
              <button onClick={() => setShareModal(null)} className="p-1 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <p className="text-sm text-gray-500 mb-4">نقش‌هایی که به این داشبورد دسترسی دارند:</p>
              <div className="space-y-2">
                {ALL_ROLES.map((r) => (
                  <label
                    key={r.value}
                    className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition"
                  >
                    <input
                      type="checkbox"
                      checked={shareRoles.includes(r.value)}
                      onChange={() => toggleShareRole(r.value)}
                      className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                    />
                    <span className="text-sm font-medium text-gray-700">{r.label}</span>
                  </label>
                ))}
              </div>
              <p className="text-[10px] text-gray-400 mt-3">بدون انتخاب = همه نقش‌ها مجازند</p>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3">
              <button
                onClick={() => setShareModal(null)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-xl transition"
              >
                انصراف
              </button>
              <button
                onClick={handleShareSave}
                className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 transition font-medium"
              >
                ذخیره دسترسی‌ها
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
