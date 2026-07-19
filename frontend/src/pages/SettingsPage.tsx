import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'
import { useToast } from '../components/Toast'
import {
  ArrowRight, Settings, Puzzle, Building2, FolderTree, Users,
  ChevronDown, ChevronRight, Plus, Pencil, Trash2, X, Check,
  ToggleLeft, ToggleRight, Zap, Save
} from 'lucide-react'

// ─── Module Management ────────────────────────────────────────────

interface AllModule {
  id: string
  label: string
}

interface CompanyModules {
  id: number
  enabled_modules: string[]
  all_modules: AllModule[]
}

const MODULE_ICONS: Record<string, React.ElementType> = {
  bi_dashboard: Zap,
  finance: Puzzle,
  crm: Users,
  db_manager: Building2,
  datasets: FolderTree,
  settings: Settings,
}

const MODULE_DESCRIPTIONS: Record<string, string> = {
  bi_dashboard: 'داشبوردها و نمودارهای هوشمند',
  finance: 'صورتحساب، پرداخت‌ها و مدیریت مالی',
  crm: 'مدیریت ارتباط با مشتریان',
  db_manager: 'مدیریت پایگاه داده و جداول',
  datasets: 'آپلود و مدیریت داده‌ها',
  settings: 'تنظیمات سازمان و ماژول‌ها',
}

function ModuleManagementTab() {
  const { toast } = useToast()
  const [companies, setCompanies] = useState<Array<{ id: number; name: string }>>([])
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null)
  const [companyModules, setCompanyModules] = useState<CompanyModules | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    fetchCompanies()
  }, [])

  useEffect(() => {
    if (selectedCompany) {
      fetchCompanyModules(selectedCompany)
    }
  }, [selectedCompany])

  const fetchCompanies = async () => {
    try {
      const res = await api.get('/auth/companies/')
      setCompanies(res.data)
      if (res.data.length > 0) {
        setSelectedCompany(res.data[0].id)
      }
    } catch {
      toast('خطا در دریافت شرکت‌ها', 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchCompanyModules = async (companyId: number) => {
    try {
      const res = await api.get(`/auth/companies/${companyId}/modules/`)
      setCompanyModules(res.data)
      setHasChanges(false)
    } catch {
      toast('خطا در دریافت ماژول‌ها', 'error')
    }
  }

  const toggleModule = (moduleId: string) => {
    if (!companyModules) return
    const current = companyModules.enabled_modules
    const updated = current.includes(moduleId)
      ? current.filter((m) => m !== moduleId)
      : [...current, moduleId]
    setCompanyModules({ ...companyModules, enabled_modules: updated })
    setHasChanges(true)
  }

  const handleSave = async () => {
    if (!selectedCompany || !companyModules) return
    setSaving(true)
    try {
      await api.put(`/auth/companies/${selectedCompany}/modules/`, {
        enabled_modules: companyModules.enabled_modules,
      })
      toast('ماژول‌ها ذخیره شدند', 'success')
      setHasChanges(false)
    } catch {
      toast('خطا در ذخیره', 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="p-12 text-center text-gray-500">در حال بارگذاری...</div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Company Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-4">انتخاب شرکت</h3>
        {companies.length === 0 ? (
          <p className="text-gray-500 text-sm">هنوز شرکتی تعریف نشده. ابتدا در تب «ساختار سازمانی» شرکت ایجاد کنید.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {companies.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCompany(c.id)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition ${
                  selectedCompany === c.id
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {c.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Module Grid */}
      {selectedCompany && companyModules && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-bold text-gray-900 dark:text-gray-100">
                ماژول‌های فعال
              </h3>
              {hasChanges && (
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'در حال ذخیره...' : 'ذخیره تغییرات'}
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {companyModules.all_modules.map((mod) => {
                const Icon = MODULE_ICONS[mod.id] || Puzzle
                const description = MODULE_DESCRIPTIONS[mod.id] || ''
                const isEnabled = companyModules.enabled_modules.includes(mod.id)
                return (
                  <div
                    key={mod.id}
                    className={`relative p-5 rounded-xl border-2 transition-all cursor-pointer ${
                      isEnabled
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                    onClick={() => toggleModule(mod.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          isEnabled ? 'bg-indigo-100 dark:bg-indigo-800' : 'bg-gray-200 dark:bg-gray-600'
                        }`}>
                          <Icon className={`w-5 h-5 ${isEnabled ? 'text-indigo-600 dark:text-indigo-300' : 'text-gray-500 dark:text-gray-400'}`} />
                        </div>
                        <div>
                          <p className={`font-medium ${isEnabled ? 'text-indigo-700 dark:text-indigo-300' : 'text-gray-700 dark:text-gray-300'}`}>
                            {mod.label}
                          </p>
                          {description && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
                          )}
                        </div>
                      </div>
                      <div className="mt-1">
                        {isEnabled ? (
                          <ToggleRight className="w-8 h-8 text-indigo-600" />
                        ) : (
                          <ToggleLeft className="w-8 h-8 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-200 dark:border-blue-800 p-4">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>نکته:</strong> ماژول‌های فعال‌شده برای کاربران این شرکت قابل مشاهده خواهند بود.
              کاربران فقط ماژول‌هایی را می‌بینند که هم در سطح شرکت فعال باشد و هم مطابق نقش کاربری دسترسی داشته باشند.
            </p>
          </div>
        </>
      )}
    </div>
  )
}

// ─── Organization Management (moved from OrganizationPage) ─────────

interface OrgUser {
  id: number
  username: string
  name: string
  role: string
}

interface Team {
  id: number
  name: string
  description: string
  manager: string | null
  manager_name: string | null
  member_count: number
  members: OrgUser[]
}

interface Division {
  id: number
  name: string
  description: string
  manager: string | null
  manager_name: string | null
  teams: Team[]
  employees: OrgUser[]
}

interface OrgCompany {
  id: number
  name: string
  description: string
  divisions: Division[]
  employees: OrgUser[]
}

interface UserOption {
  id: number
  username: string
  first_name: string
  last_name: string
  role: string
}

function OrganizationTab() {
  const { toast } = useToast()
  const [tree, setTree] = useState<OrgCompany[]>([])
  const [users, setUsers] = useState<UserOption[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [modalType, setModalType] = useState<'company' | 'division' | 'team' | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState({ name: '', description: '', manager: 0, company: 0, division: 0 })

  useEffect(() => { fetchData() }, [])

  const fetchData = async () => {
    try {
      const [treeRes, usersRes] = await Promise.all([
        api.get('/auth/org-tree/'),
        api.get('/auth/users/'),
      ])
      setTree(treeRes.data)
      setUsers(usersRes.data)
    } catch {
      toast('خطا در دریافت اطلاعات', 'error')
    } finally {
      setLoading(false)
    }
  }

  const toggle = (key: string) => setExpanded((p) => ({ ...p, [key]: !p[key] }))

  const openCreate = (type: 'company' | 'division' | 'team', parentId?: number) => {
    setModalType(type)
    setEditingId(null)
    setForm({ name: '', description: '', manager: 0, company: type === 'division' ? parentId || 0 : 0, division: type === 'team' ? parentId || 0 : 0 })
  }

  const openEdit = (type: 'company' | 'division' | 'team', item: { id: number; name: string; description?: string; manager?: string | null }, parentId?: number) => {
    setModalType(type)
    setEditingId(item.id)
    const mgrUser = users.find((u) => u.username === item.manager)
    setForm({ name: item.name, description: item.description || '', manager: mgrUser?.id || 0, company: type === 'division' ? parentId || 0 : 0, division: type === 'team' ? parentId || 0 : 0 })
  }

  const handleSubmit = async () => {
    if (!form.name.trim()) { toast('نام الزامی است', 'error'); return }
    try {
      const payload: Record<string, unknown> = { name: form.name, description: form.description }
      if (form.manager) payload.manager = form.manager
      if (modalType === 'company') {
        if (editingId) await api.put(`/auth/companies/${editingId}/`, payload)
        else await api.post('/auth/companies/', payload)
      } else if (modalType === 'division') {
        payload.company = form.company
        if (editingId) await api.put(`/auth/divisions/${editingId}/`, payload)
        else await api.post('/auth/divisions/', payload)
      } else if (modalType === 'team') {
        payload.division = form.division
        if (editingId) await api.put(`/auth/teams/${editingId}/`, payload)
        else await api.post('/auth/teams/', payload)
      }
      toast(editingId ? 'به‌روزرسانی شد' : 'ایجاد شد', 'success')
      setModalType(null)
      fetchData()
    } catch { toast('خطا در ذخیره', 'error') }
  }

  const handleDelete = async (type: 'company' | 'division' | 'team', id: number, name: string) => {
    if (!window.confirm(`آیا از حذف «${name}» اطمینان دارید؟`)) return
    try {
      if (type === 'company') await api.delete(`/auth/companies/${id}/`)
      else if (type === 'division') await api.delete(`/auth/divisions/${id}/`)
      else await api.delete(`/auth/teams/${id}/`)
      toast('حذف شد', 'success')
      fetchData()
    } catch { toast('خطا در حذف', 'error') }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-gray-900 dark:text-gray-100">درخت سازمانی</h3>
        <button onClick={() => openCreate('company')} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm font-medium">
          <Building2 className="w-4 h-4" /> شرکت جدید
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-gray-500">در حال بارگذاری...</div>
      ) : tree.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-4">هنوز شرکتی تعریف نشده</p>
          <button onClick={() => openCreate('company')} className="px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm font-medium">ایجاد اولین شرکت</button>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="divide-y divide-gray-50 dark:divide-gray-700">
            {tree.map((company) => {
              const compKey = `c${company.id}`
              const isCompOpen = expanded[compKey] !== false
              return (
                <div key={company.id}>
                  <div className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition flex items-center justify-between">
                    <div className="flex items-center gap-3 cursor-pointer" onClick={() => toggle(compKey)}>
                      {isCompOpen ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                      <div className="w-8 h-8 bg-indigo-100 dark:bg-indigo-800 rounded-lg flex items-center justify-center"><Building2 className="w-4 h-4 text-indigo-600 dark:text-indigo-300" /></div>
                      <div>
                        <p className="text-sm font-bold text-gray-900 dark:text-gray-100">{company.name}</p>
                        <p className="text-xs text-gray-500">{company.divisions.length} واحد · {company.employees.length} کارمند مستقیم</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button onClick={() => openCreate('division', company.id)} className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition" title="افزودن واحد"><Plus className="w-4 h-4" /></button>
                      <button onClick={() => openEdit('company', company)} className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition"><Pencil className="w-4 h-4" /></button>
                      <button onClick={() => handleDelete('company', company.id, company.name)} className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </div>
                  {isCompOpen && (
                    <div className="mr-8">
                      {company.divisions.map((div) => {
                        const divKey = `d${div.id}`
                        const isDivOpen = expanded[divKey] === true
                        return (
                          <div key={div.id}>
                            <div className="px-6 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition flex items-center justify-between border-r-2 border-indigo-100 dark:border-indigo-800">
                              <div className="flex items-center gap-3 cursor-pointer" onClick={() => toggle(divKey)}>
                                {isDivOpen ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />}
                                <div className="w-7 h-7 bg-blue-50 dark:bg-blue-900/30 rounded-lg flex items-center justify-center"><FolderTree className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" /></div>
                                <div>
                                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{div.name}</p>
                                  <p className="text-[11px] text-gray-500">{div.manager_name ? `مدیر: ${div.manager_name}` : 'بدون مدیر'} · {div.teams.length} تیم</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <button onClick={() => openCreate('team', div.id)} className="p-1 text-gray-400 hover:text-blue-500 rounded transition"><Plus className="w-3.5 h-3.5" /></button>
                                <button onClick={() => openEdit('division', div, company.id)} className="p-1 text-gray-400 hover:text-blue-500 rounded transition"><Pencil className="w-3.5 h-3.5" /></button>
                                <button onClick={() => handleDelete('division', div.id, div.name)} className="p-1 text-gray-400 hover:text-red-500 rounded transition"><Trash2 className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                            {isDivOpen && (
                              <div className="mr-8">
                                {div.teams.map((team) => (
                                  <div key={team.id} className="px-6 py-2 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition flex items-center justify-between border-r-2 border-blue-100 dark:border-blue-800">
                                    <div className="flex items-center gap-3">
                                      <Users className="w-3.5 h-3.5 text-emerald-500" />
                                      <div>
                                        <p className="text-xs font-medium text-gray-700 dark:text-gray-300">{team.name}</p>
                                        <p className="text-[10px] text-gray-500">{team.manager_name ? `سرپرست: ${team.manager_name}` : 'بدون سرپرست'} · {team.member_count} عضو</p>
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <button onClick={() => openEdit('team', team, div.id)} className="p-0.5 text-gray-400 hover:text-emerald-500 rounded transition"><Pencil className="w-3 h-3" /></button>
                                      <button onClick={() => handleDelete('team', team.id, team.name)} className="p-0.5 text-gray-400 hover:text-red-500 rounded transition"><Trash2 className="w-3 h-3" /></button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Modal */}
      {modalType && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" dir="rtl">
          <div className="absolute inset-0 bg-black/40" onClick={() => setModalType(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h3 className="font-bold text-gray-900 dark:text-gray-100">{editingId ? 'ویرایش' : 'ایجاد'} {modalType === 'company' ? 'شرکت' : modalType === 'division' ? 'واحد' : 'تیم'}</h3>
              <button onClick={() => setModalType(null)} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">نام *</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">توضیحات</label>
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">مدیر</label>
                <select value={form.manager || ''} onChange={(e) => setForm({ ...form, manager: Number(e.target.value) })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 outline-none">
                  <option value="">انتخاب مدیر...</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>{u.first_name || u.last_name ? `${u.first_name} ${u.last_name}` : u.username} (@{u.username})</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-end gap-3">
              <button onClick={() => setModalType(null)} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition">انصراف</button>
              <button onClick={handleSubmit} className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 transition font-medium flex items-center gap-2">
                <Check className="w-4 h-4" /> {editingId ? 'ذخیره' : 'ایجاد'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Main Settings Page ───────────────────────────────────────────

export default function SettingsPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'modules' | 'org'>('modules')

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'ceo')) {
      navigate('/dashboards')
    }
  }, [user, navigate])

  if (user?.role !== 'admin' && user?.role !== 'ceo') return null

  const tabs = [
    { id: 'modules' as const, label: 'مدیریت ماژول‌ها', icon: Puzzle },
    { id: 'org' as const, label: 'ساختار سازمانی', icon: Building2 },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" dir="rtl">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link to="/launcher" className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
            <ArrowRight className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center">
              <Settings className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">تنظیمات</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">مدیریت ماژول‌ها و ساختار سازمانی</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex items-center gap-1 mb-6">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${
                  activeTab === tab.id
                    ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                    : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" /> {tab.label}
              </button>
            )
          })}
        </div>

        {/* Tab Content */}
        {activeTab === 'modules' && <ModuleManagementTab />}
        {activeTab === 'org' && <OrganizationTab />}
      </main>
    </div>
  )
}
