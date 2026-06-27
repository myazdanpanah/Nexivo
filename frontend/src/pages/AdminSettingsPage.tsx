import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { ArrowRight, Users, Pencil, Trash2, X, Shield, UserPlus, Trash, History, ChevronDown, ChevronUp } from 'lucide-react'
import { ALL_ROLES, ROLE_MAP } from '../utils/roles'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'finance' | 'sales' | 'ceo' | 'admin'
  department: string
  company: number | null
  company_name: string | null
  division: number | null
  division_name: string | null
  team: number | null
  team_name: string | null
  reports_to: number | null
  reports_to_name: string | null
}

interface AuditLog {
  id: number
  action: string
  action_display: string
  user: string | null
  target_type: string
  target_id: string
  target_name: string
  old_value: Record<string, unknown>
  new_value: Record<string, unknown>
  details: Record<string, unknown>
  created_at: string
}

interface OrgCompany { id: number; name: string }
interface OrgDivision { id: number; name: string; company: number }
interface OrgTeam { id: number; name: string; division: number }

const ACTION_LABELS: Record<string, string> = {
  dashboard_share: 'اشتراک‌گذاری داشبورد',
  dashboard_create: 'ساخت داشبورد',
  dashboard_delete: 'حذف داشبورد',
  page_access_update: 'بروزرسانی دسترسی صفحه',
  filter_access_update: 'بروزرسانی دسترسی فیلتر',
  user_role_change: 'تغییر نقش کاربر',
}

const ACTION_COLORS: Record<string, string> = {
  dashboard_share: 'bg-blue-100 text-blue-700',
  dashboard_create: 'bg-green-100 text-green-700',
  dashboard_delete: 'bg-red-100 text-red-700',
  page_access_update: 'bg-amber-100 text-amber-700',
  filter_access_update: 'bg-purple-100 text-purple-700',
  user_role_change: 'bg-indigo-100 text-indigo-700',
}

const ROLE_OPTIONS = ALL_ROLES

export default function AdminSettingsPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [clearing, setClearing] = useState(false)
  const [activeTab, setActiveTab] = useState<'users' | 'audit'>('users')
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [auditLoading, setAuditLoading] = useState(true)
  const [expandedLog, setExpandedLog] = useState<number | null>(null)
  const [companies, setCompanies] = useState<OrgCompany[]>([])
  const [divisions, setDivisions] = useState<OrgDivision[]>([])
  const [teams, setTeams] = useState<OrgTeam[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [form, setForm] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'sales' as string,
    department: '',
    password: '',
    company: null as number | null,
    division: null as number | null,
    team: null as number | null,
    reports_to: null as number | null,
  })

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'ceo')) {
      navigate('/dashboards')
      return
    }
    fetchUsers()
    fetchAuditLogs()
    fetchOrgData()
  }, [user, navigate])

  const fetchOrgData = async () => {
    try {
      const [compRes, divRes, teamRes, userRes] = await Promise.all([
        api.get('/auth/companies/'),
        api.get('/auth/divisions/'),
        api.get('/auth/teams/'),
        api.get('/auth/users/'),
      ])
      setCompanies(compRes.data)
      setDivisions(divRes.data)
      setTeams(teamRes.data)
      setAllUsers(userRes.data)
    } catch { /* ignore */ }
  }

  const fetchAuditLogs = async () => {
    try {
      const res = await api.get('/dashboards/audit-log/')
      setAuditLogs(res.data)
    } catch { /* ignore */ }
    finally { setAuditLoading(false) }
  }

  const fetchUsers = async () => {
    try {
      const res = await api.get('/auth/users/')
      setUsers(res.data)
    } catch {
      toast('خطا در دریافت لیست کاربران', 'error')
    } finally {
      setLoading(false)
    }
  }

  const filteredDivisions = divisions.filter((d) => !form.company || d.company === form.company)
  const filteredTeams = teams.filter((t) => !form.division || t.division === form.division)

  const openCreateModal = () => {
    setEditingUser(null)
    setForm({ username: '', email: '', first_name: '', last_name: '', role: 'sales', department: '', password: '', company: null, division: null, team: null, reports_to: null })
    setShowModal(true)
  }

  const openEditModal = (u: User) => {
    setEditingUser(u)
    setForm({
      username: u.username,
      email: u.email,
      first_name: u.first_name,
      last_name: u.last_name,
      role: u.role,
      department: u.department,
      password: '',
      company: u.company,
      division: u.division,
      team: u.team,
      reports_to: u.reports_to,
    })
    setShowModal(true)
  }

  const handleSubmit = async () => {
    if (!form.username || !form.email) {
      toast('نام کاربری و ایمیل الزامی است', 'error')
      return
    }

    try {
      if (editingUser) {
        const payload: Record<string, unknown> = {
          username: form.username,
          email: form.email,
          first_name: form.first_name,
          last_name: form.last_name,
          role: form.role,
          department: form.department,
          company: form.company,
          division: form.division,
          team: form.team,
          reports_to: form.reports_to,
        }
        await api.put(`/auth/users/${editingUser.id}/`, payload)
        toast('کاربر به‌روزرسانی شد', 'success')
      } else {
        if (!form.password || form.password.length < 8) {
          toast('رمز عبور باید حداقل ۸ کاراکتر باشد', 'error')
          return
        }
        await api.post('/auth/users/', {
          username: form.username,
          email: form.email,
          first_name: form.first_name,
          last_name: form.last_name,
          role: form.role,
          department: form.department,
          password: form.password,
          company: form.company,
          division: form.division,
          team: form.team,
          reports_to: form.reports_to,
        })
        toast('کاربر جدید ساخته شد', 'success')
      }
      setShowModal(false)
      fetchUsers()
      fetchOrgData()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { error?: string } } }
      toast(axiosErr.response?.data?.error || 'خطا در ذخیره', 'error')
    }
  }

  const handleDelete = async (u: User) => {
    if (u.id === user?.id) {
      toast('امکان حذف خود وجود ندارد', 'error')
      return
    }
    if (!window.confirm(`آیا از حذف کاربر «${u.username}» اطمینان دارید؟`)) return

    try {
      await api.delete(`/auth/users/${u.id}/`)
      toast('کاربر حذف شد', 'success')
      fetchUsers()
    } catch {
      toast('خطا در حذف کاربر', 'error')
    }
  }

  const handleClearAll = async () => {
    if (!window.confirm('⚠️ آیا از حذف تمام داشبوردها و داده‌ها اطمینان دارید؟ این عمل غیرقابل بازگشت است.')) return
    if (!window.confirm('⚠️ این آخرین هشدار است! تمام داده‌ها حذف خواهند شد. تایید کنید:')) return
    setClearing(true)
    try {
      await api.delete('/dashboards/clear-all/', { data: { confirm: true } })
      toast('تمام داشبوردها و نمودارها حذف شدند', 'success')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { error?: string } } }
      toast(axiosErr.response?.data?.error || 'خطا در حذف داده‌ها', 'error')
    } finally {
      setClearing(false)
    }
  }

  if (user?.role !== 'admin' && user?.role !== 'ceo') {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" dir="rtl">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboards" className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">مدیریت کاربران</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">ایجاد، ویرایش و حذف نقش‌ها و دسترسی‌ها</p>
              </div>
            </div>
          </div>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm font-medium"
          >
            <UserPlus className="w-4 h-4" />
            کاربر جدید
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {ROLE_OPTIONS.map((r) => {
            const count = users.filter((u) => u.role === r.value).length
            return (
              <div key={r.value} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${r.color}`}>
                    <Users className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{count}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{r.label}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Danger Zone */}
        {user?.isStaff && (
          <div className="mb-8 bg-white dark:bg-gray-800 rounded-2xl border-2 border-red-200 dark:border-red-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-red-100 flex items-center justify-between">
              <div>
                <h2 className="font-bold text-red-700 dark:text-red-400">منطقه خطر</h2>
                <p className="text-xs text-red-400">حذف تمام داشبوردها، صفحات و نمودارها</p>
              </div>
              <button
                onClick={handleClearAll}
                disabled={clearing}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 transition text-sm font-medium disabled:opacity-50"
              >
                <Trash className="w-4 h-4" />
                {clearing ? 'در حال حذف...' : 'حذف همه داده‌ها'}
              </button>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-6">
          <button onClick={() => setActiveTab('users')} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${activeTab === 'users' ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}>
            <Users className="w-4 h-4" /> کاربران
          </button>
          <button onClick={() => setActiveTab('audit')} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${activeTab === 'audit' ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}>
            <History className="w-4 h-4" /> تاریخچه تغییرات
          </button>
        </div>

        {/* Users Table */}
        {activeTab === 'users' && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h2 className="font-bold text-gray-900 dark:text-gray-100">لیست کاربران ({users.length})</h2>
            </div>
            {loading ? (
              <div className="p-12 text-center text-gray-500">در حال بارگذاری...</div>
            ) : users.length === 0 ? (
              <div className="p-12 text-center">
                <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">هنوز کاربری وجود ندارد</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-right text-xs text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
                      <th className="px-6 py-3 font-medium">کاربر</th>
                      <th className="px-6 py-3 font-medium">ایمیل</th>
                      <th className="px-6 py-3 font-medium">نقش</th>
                      <th className="px-6 py-3 font-medium">ساختار سازمانی</th>
                      <th className="px-6 py-3 font-medium">عملیات</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {users.map((u) => {
                      const roleInfo = ROLE_MAP[u.role] || ROLE_OPTIONS[3]
                      return (
                        <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {u.first_name || u.last_name ? `${u.first_name} ${u.last_name}` : u.username}
                              </p>
                              <p className="text-xs text-gray-400">@{u.username}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{u.email}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex px-2.5 py-0.5 rounded-lg text-xs font-medium ${roleInfo.color}`}>{roleInfo.label}</span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex flex-wrap gap-1">
                              {u.company_name && <span className="px-1.5 py-0.5 bg-indigo-50 text-indigo-600 rounded text-[10px]">{u.company_name}</span>}
                              {u.division_name && <span className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-[10px]">{u.division_name}</span>}
                              {u.team_name && <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded text-[10px]">{u.team_name}</span>}
                              {u.reports_to_name && <span className="px-1.5 py-0.5 bg-amber-50 text-amber-600 rounded text-[10px]">↑ {u.reports_to_name}</span>}
                              {!u.company_name && !u.division_name && !u.team_name && <span className="text-xs text-gray-400">-</span>}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-1">
                              <button onClick={() => openEditModal(u)} className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded-lg transition" title="ویرایش"><Pencil className="w-4 h-4" /></button>
                              {u.id !== user?.id && (
                                <button onClick={() => handleDelete(u)} className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition" title="حذف"><Trash2 className="w-4 h-4" /></button>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Audit Log */}
        {activeTab === 'audit' && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h2 className="font-bold text-gray-900 dark:text-gray-100">تاریخچه تغییرات دسترسی ({auditLogs.length})</h2>
            </div>
            {auditLoading ? (
              <div className="p-12 text-center text-gray-500">در حال بارگذاری...</div>
            ) : auditLogs.length === 0 ? (
              <div className="p-12 text-center">
                <History className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">هنوز تغییری ثبت نشده</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {auditLogs.map((log) => (
                  <div key={log.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`inline-flex px-2.5 py-0.5 rounded-lg text-xs font-medium ${ACTION_COLORS[log.action] || 'bg-gray-100 text-gray-700'}`}>
                          {ACTION_LABELS[log.action] || log.action_display}
                        </span>
                        <div>
                          <p className="text-sm text-gray-900 dark:text-gray-100">
                            <span className="font-medium">{log.target_type}</span>
                            {' '}«{log.target_name || log.target_id}»
                          </p>
                          <p className="text-xs text-gray-400">
                            توسط {log.user || 'سیستم'} · {new Date(log.created_at).toLocaleString('fa-IR')}
                          </p>
                        </div>
                      </div>
                      <button onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)} className="p-1 text-gray-400 hover:text-gray-600 transition">
                        {expandedLog === log.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                    {expandedLog === log.id && (
                      <div className="mt-3 pl-6 border-r-2 border-indigo-200 pr-3 space-y-2">
                        {Object.keys(log.old_value).length > 0 && (
                          <div>
                            <span className="text-[10px] text-gray-400 uppercase tracking-wide">قبل:</span>
                            <pre className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg p-2 mt-1 overflow-x-auto">{JSON.stringify(log.old_value, null, 2)}</pre>
                          </div>
                        )}
                        {Object.keys(log.new_value).length > 0 && (
                          <div>
                            <span className="text-[10px] text-gray-400 uppercase tracking-wide">بعد:</span>
                            <pre className="text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded-lg p-2 mt-1 overflow-x-auto">{JSON.stringify(log.new_value, null, 2)}</pre>
                          </div>
                        )}
                        {Object.keys(log.details).length > 0 && (
                          <div>
                            <span className="text-[10px] text-gray-400 uppercase tracking-wide">جزئیات:</span>
                            <pre className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 mt-1 overflow-x-auto">{JSON.stringify(log.details, null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" dir="rtl">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowModal(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
              <h3 className="font-bold text-gray-900 dark:text-gray-100">{editingUser ? 'ویرایش کاربر' : 'کاربر جدید'}</h3>
              <button onClick={() => setShowModal(false)} className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"><X className="w-5 h-5" /></button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">نام</label>
                  <input type="text" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">نام خانوادگی</label>
                  <input type="text" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" />
                </div>
              </div>

              <div>                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">نام کاربری *</label>
                  <input type="text" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" disabled={!!editingUser} />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">ایمیل *</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">نقش *</label>
                <div className="grid grid-cols-2 gap-2">
                  {ROLE_OPTIONS.map((r) => (
                    <button key={r.value} type="button" onClick={() => setForm({ ...form, role: r.value })} className={`p-3 rounded-xl border-2 text-sm font-medium transition ${form.role === r.value ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'}`}>
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">بخش</label>
                <input type="text" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" placeholder="مثلاً: فروش، مالی، ..." />
              </div>

              {/* Org Hierarchy */}
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl space-y-3">
                <p className="text-xs font-bold text-gray-700 dark:text-gray-300">🏢 ساختار سازمانی</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-1">شرکت</label>
                    <select value={form.company || ''} onChange={(e) => setForm({ ...form, company: Number(e.target.value) || null, division: null, team: null })} className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 outline-none">
                      <option value="">بدون شرکت</option>
                      {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-1">واحد</label>
                    <select value={form.division || ''} onChange={(e) => setForm({ ...form, division: Number(e.target.value) || null, team: null })} className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" disabled={!form.company}>
                      <option value="">بدون واحد</option>
                      {filteredDivisions.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-1">تیم</label>
                    <select value={form.team || ''} onChange={(e) => setForm({ ...form, team: Number(e.target.value) || null })} className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" disabled={!form.division}>
                      <option value="">بدون تیم</option>
                      {filteredTeams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-1">گزارش‌دهی به</label>
                    <select value={form.reports_to || ''} onChange={(e) => setForm({ ...form, reports_to: Number(e.target.value) || null })} className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 outline-none">
                      <option value="">بدون مدیر</option>
                      {allUsers.filter((u) => u.id !== editingUser?.id).map((u) => (
                        <option key={u.id} value={u.id}>{u.first_name || u.last_name ? `${u.first_name} ${u.last_name}` : u.username}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {!editingUser && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">رمز عبور *</label>
                  <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" placeholder="حداقل ۸ کاراکتر" />
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-end gap-3">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition">انصراف</button>
              <button onClick={handleSubmit} className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 transition font-medium">
                {editingUser ? 'ذخیره تغییرات' : 'ساخت کاربر'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
