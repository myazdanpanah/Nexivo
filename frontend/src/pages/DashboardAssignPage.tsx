import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { ArrowRight, UserPlus, Trash2, Pencil, X, Shield, Filter, Eye, ChevronDown, ChevronUp, Users, Check } from 'lucide-react'

interface Dashboard {
  id: number
  name: string
  description: string
  owner_name: string
  pages: Array<{ id: number; name: string; widgets: unknown[] }>
  allowed_roles: string[]
}

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  department: string
}

interface Assignment {
  id: number
  dashboard: number
  dashboard_name: string
  assigned_to: number
  assigned_to_username: string
  assigned_to_name: string
  assigned_by: number | null
  assigned_by_username: string | null
  data_filters: Array<{ col: string; op: string; val: string | string[] }>
  visible_pages: number[]
  visible_filter_controls: string[]
  notes: string
  is_active: boolean
  created_at: string
}

interface DataFilter {
  col: string
  op: string
  val: string | string[]
}

const FILTER_OPERATORS = [
  { value: 'eq', label: 'برابر با' },
  { value: 'neq', label: 'نابرابر با' },
  { value: 'contains', label: 'شامل' },
  { value: 'gt', label: 'بزرگتر از' },
  { value: 'gte', label: 'بزرگتر یا مساوی' },
  { value: 'lt', label: 'کوچکتر از' },
  { value: 'lte', label: 'کوچکتر یا مساوی' },
  { value: 'starts_with', label: 'شروع با' },
  { value: 'ends_with', label: 'پایان با' },
  { value: 'in', label: 'در لیست' },
]

const ROLE_LABELS: Record<string, string> = {
  ceo: 'مدیرعامل',
  finance: 'مالی',
  sales: 'فروش',
  admin: 'مدیر سیستم',
}

export default function DashboardAssignPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToast()

  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [dashboards, setDashboards] = useState<Dashboard[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  // Form state
  const [form, setForm] = useState({
    dashboard: 0,
    assigned_to: 0,
    data_filters: [] as DataFilter[],
    visible_pages: [] as number[],
    notes: '',
    is_active: true,
  })

  const selectedDashboard = dashboards.find((d) => d.id === form.dashboard)

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'ceo')) {
      navigate('/dashboards')
      return
    }
    fetchData()
  }, [user, navigate])

  const fetchData = async () => {
    try {
      const [assignRes, dashRes, userRes] = await Promise.all([
        api.get('/dashboards/assignments/'),
        api.get('/dashboards/'),
        api.get('/auth/users/'),
      ])
      setAssignments(assignRes.data)
      setDashboards(dashRes.data)
      setUsers(userRes.data)
    } catch {
      toast('خطا در دریافت اطلاعات', 'error')
    } finally {
      setLoading(false)
    }
  }

  const openCreateModal = () => {
    setEditingAssignment(null)
    setForm({
      dashboard: 0,
      assigned_to: 0,
      data_filters: [],
      visible_pages: [],
      notes: '',
      is_active: true,
    })
    setShowModal(true)
  }

  const openEditModal = (assignment: Assignment) => {
    setEditingAssignment(assignment)
    setForm({
      dashboard: assignment.dashboard,
      assigned_to: assignment.assigned_to,
      data_filters: assignment.data_filters || [],
      visible_pages: assignment.visible_pages || [],
      notes: assignment.notes || '',
      is_active: assignment.is_active,
    })
    setShowModal(true)
  }

  const handleSubmit = async () => {
    if (!form.dashboard || !form.assigned_to) {
      toast('انتخاب داشبورد و کاربر الزامی است', 'error')
      return
    }

    try {
      const payload = {
        dashboard: form.dashboard,
        assigned_to: form.assigned_to,
        data_filters: form.data_filters,
        visible_pages: form.visible_pages,
        notes: form.notes,
        is_active: form.is_active,
      }

      if (editingAssignment) {
        await api.put(`/dashboards/assignments/${editingAssignment.id}/`, payload)
        toast('تخصیص به‌روزرسانی شد', 'success')
      } else {
        await api.post('/dashboards/assignments/', payload)
        toast('تخصیص جدید ایجاد شد', 'success')
      }
      setShowModal(false)
      fetchData()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { error?: string } } }
      toast(axiosErr.response?.data?.error || 'خطا در ذخیره', 'error')
    }
  }

  const handleDelete = async (assignment: Assignment) => {
    if (!window.confirm(`آیا از حذف تخصیص «${assignment.dashboard_name}» برای «${assignment.assigned_to_name || assignment.assigned_to_username}» اطمینان دارید؟`)) return
    try {
      await api.delete(`/dashboards/assignments/${assignment.id}/`)
      toast('تخصیص حذف شد', 'success')
      fetchData()
    } catch {
      toast('خطا در حذف تخصیص', 'error')
    }
  }

  const addDataFilter = () => {
    setForm((prev) => ({
      ...prev,
      data_filters: [...prev.data_filters, { col: '', op: 'eq', val: '' }],
    }))
  }

  const updateDataFilter = (index: number, field: keyof DataFilter, value: string) => {
    setForm((prev) => ({
      ...prev,
      data_filters: prev.data_filters.map((f, i) =>
        i === index ? { ...f, [field]: value } : f
      ),
    }))
  }

  const removeDataFilter = (index: number) => {
    setForm((prev) => ({
      ...prev,
      data_filters: prev.data_filters.filter((_, i) => i !== index),
    }))
  }

  const togglePageVisibility = (pageId: number) => {
    setForm((prev) => ({
      ...prev,
      visible_pages: prev.visible_pages.includes(pageId)
        ? prev.visible_pages.filter((id) => id !== pageId)
        : [...prev.visible_pages, pageId],
    }))
  }

  if (user?.role !== 'admin' && user?.role !== 'ceo') {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboards" className="p-2 text-gray-400 hover:text-gray-600 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">تخصیص داشبورد</h1>
                <p className="text-xs text-gray-500">تعریف دسترسی کارکنان به داشبوردها با فیلترهای داده خاص</p>
              </div>
            </div>
          </div>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition text-sm font-medium"
          >
            <UserPlus className="w-4 h-4" />
            تخصیص جدید
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                <Users className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{assignments.length}</p>
                <p className="text-xs text-gray-500">تخصیص فعال</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                <Shield className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{dashboards.length}</p>
                <p className="text-xs text-gray-500">داشبورد</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                <Filter className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {assignments.filter((a) => a.data_filters?.length > 0).length}
                </p>
                <p className="text-xs text-gray-500">با فیلتر داده</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <Eye className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {assignments.filter((a) => a.visible_pages?.length > 0).length}
                </p>
                <p className="text-xs text-gray-500">با محدودیت صفحه</p>
              </div>
            </div>
          </div>
        </div>

        {/* Assignments List */}
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="font-bold text-gray-900">لیست تخصیص‌ها ({assignments.length})</h2>
          </div>

          {loading ? (
            <div className="p-12 text-center text-gray-500">در حال بارگذاری...</div>
          ) : assignments.length === 0 ? (
            <div className="p-12 text-center">
              <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 mb-4">هنوز تخصیصی ایجاد نشده</p>
              <button
                onClick={openCreateModal}
                className="px-4 py-2 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition text-sm font-medium"
              >
                ایجاد اولین تخصیص
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {assignments.map((assignment) => (
                <div key={assignment.id} className="px-6 py-4 hover:bg-gray-50 transition">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center text-indigo-700 font-bold text-sm">
                        {(assignment.assigned_to_name || assignment.assigned_to_username).charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {assignment.assigned_to_name || assignment.assigned_to_username}
                          <span className="text-gray-400 mr-2 text-xs">@{assignment.assigned_to_username}</span>
                        </p>
                        <p className="text-xs text-gray-500">
                          داشبورد: <span className="font-medium">{assignment.dashboard_name}</span>
                          {assignment.assigned_by_username && (
                            <span className="mr-2">· توسط {assignment.assigned_by_username}</span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-medium ${
                        assignment.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {assignment.is_active ? 'فعال' : 'غیرفعال'}
                      </span>
                      {assignment.data_filters?.length > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 rounded-lg text-xs font-medium">
                          <Filter className="w-3 h-3" />
                          {assignment.data_filters.length} فیلتر
                        </span>
                      )}
                      {assignment.visible_pages?.length > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-lg text-xs font-medium">
                          <Eye className="w-3 h-3" />
                          {assignment.visible_pages.length} صفحه
                        </span>
                      )}
                      <button
                        onClick={() => setExpandedId(expandedId === assignment.id ? null : assignment.id)}
                        className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition"
                      >
                        {expandedId === assignment.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => openEditModal(assignment)}
                        className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded-lg transition"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(assignment)}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Expanded details */}
                  {expandedId === assignment.id && (
                    <div className="mt-4 pl-6 border-r-2 border-indigo-200 pr-3 space-y-3">
                      {/* Data Filters */}
                      {assignment.data_filters?.length > 0 && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-500 mb-2">فیلترهای داده:</h4>
                          <div className="space-y-1">
                            {assignment.data_filters.map((f, i) => (
                              <div key={i} className="flex items-center gap-2 text-xs bg-amber-50 px-3 py-1.5 rounded-lg">
                                <span className="font-medium text-amber-800">{f.col}</span>
                                <span className="text-amber-600">{FILTER_OPERATORS.find((op) => op.value === f.op)?.label || f.op}</span>
                                <span className="text-amber-700">{Array.isArray(f.val) ? f.val.join(', ') : f.val}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Visible Pages */}
                      {assignment.visible_pages?.length > 0 && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-500 mb-2">صفحات قابل مشاهده:</h4>
                          <div className="flex flex-wrap gap-1">
                            {assignment.visible_pages.map((pageId) => {
                              const page = selectedDashboard?.pages?.find((p) => p.id === pageId) ||
                                dashboards.find((d) => d.id === assignment.dashboard)?.pages?.find((p) => p.id === pageId)
                              return (
                                <span key={pageId} className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                                  {page?.name || `صفحه ${pageId}`}
                                </span>
                              )
                            })}
                          </div>
                        </div>
                      )}

                      {/* Notes */}
                      {assignment.notes && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-500 mb-1">یادداشت:</h4>
                          <p className="text-xs text-gray-600 bg-gray-50 px-3 py-2 rounded-lg">{assignment.notes}</p>
                        </div>
                      )}

                      {/* No restrictions */}
                      {(!assignment.data_filters?.length && !assignment.visible_pages?.length) && (
                        <p className="text-xs text-gray-400 italic">بدون محدودیت - تمام داده‌ها و صفحات قابل مشاهده</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" dir="rtl">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowModal(false)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 sticky top-0 bg-white z-10">
              <h3 className="font-bold text-gray-900">
                {editingAssignment ? 'ویرایش تخصیص' : 'تخصیص جدید'}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-1 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Dashboard selector */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">داشبورد *</label>
                <select
                  value={form.dashboard || ''}
                  onChange={(e) => {
                    const dashId = Number(e.target.value)
                    setForm((prev) => ({ ...prev, dashboard: dashId, visible_pages: [] }))
                  }}
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                  disabled={!!editingAssignment}
                >
                  <option value="">انتخاب داشبورد...</option>
                  {dashboards.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              {/* User selector */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">کاربر *</label>
                <select
                  value={form.assigned_to || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, assigned_to: Number(e.target.value) }))}
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                  disabled={!!editingAssignment}
                >
                  <option value="">انتخاب کاربر...</option>
                  {users.filter((u) => u.id !== user?.id).map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.first_name || u.last_name ? `${u.first_name} ${u.last_name}` : u.username}
                      {' '}(@{u.username}) - {ROLE_LABELS[u.role] || u.role}
                    </option>
                  ))}
                </select>
              </div>

              {/* Page Visibility */}
              {selectedDashboard && selectedDashboard.pages && selectedDashboard.pages.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2">
                    صفحات قابل مشاهده
                    <span className="text-gray-400 font-normal mr-1">(بدون انتخاب = همه صفحات)</span>
                  </label>
                  <div className="space-y-1">
                    {selectedDashboard.pages.map((page) => (
                      <label
                        key={page.id}
                        className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition"
                      >
                        <input
                          type="checkbox"
                          checked={form.visible_pages.includes(page.id)}
                          onChange={() => togglePageVisibility(page.id)}
                          className="w-4 h-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
                        />
                        <div>
                          <span className="text-sm font-medium text-gray-700">{page.name}</span>
                          <span className="text-xs text-gray-400 mr-2">{page.widgets?.length || 0} نمودار</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Data Filters */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium text-gray-700">
                    فیلترهای ردیف داده
                    <span className="text-gray-400 font-normal mr-1">(محدود کردن داده‌های قابل مشاهده)</span>
                  </label>
                  <button
                    onClick={addDataFilter}
                    className="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                  >
                    + افزودن فیلتر
                  </button>
                </div>
                {form.data_filters.length > 0 ? (
                  <div className="space-y-2">
                    {form.data_filters.map((filter, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={filter.col}
                          onChange={(e) => updateDataFilter(index, 'col', e.target.value)}
                          placeholder="نام ستون"
                          className="flex-1 px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                        />
                        <select
                          value={filter.op}
                          onChange={(e) => updateDataFilter(index, 'op', e.target.value)}
                          className="px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                        >
                          {FILTER_OPERATORS.map((op) => (
                            <option key={op.value} value={op.value}>{op.label}</option>
                          ))}
                        </select>
                        <input
                          type="text"
                          value={filter.val}
                          onChange={(e) => updateDataFilter(index, 'val', e.target.value)}
                          placeholder="مقدار"
                          className="flex-1 px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                        />
                        <button
                          onClick={() => removeDataFilter(index)}
                          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 bg-gray-50 px-3 py-2 rounded-lg">بدون فیلتر - تمام داده‌ها قابل مشاهده</p>
                )}
              </div>

              {/* Active toggle */}
              <div className="flex items-center justify-between p-4 rounded-xl border border-gray-200">
                <div>
                  <p className="text-sm font-medium text-gray-700">وضعیت تخصیص</p>
                  <p className="text-xs text-gray-500">غیرفعال کردن این تخصیص بدون حذف آن</p>
                </div>
                <button
                  type="button"
                  onClick={() => setForm((prev) => ({ ...prev, is_active: !prev.is_active }))}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                    form.is_active ? 'bg-emerald-600' : 'bg-gray-300'
                  }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                    form.is_active ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">یادداشت مدیر</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
                  rows={3}
                  placeholder="توضیحات درباره این تخصیص..."
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none resize-none"
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3 sticky bottom-0 bg-white">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-xl transition"
              >
                انصراف
              </button>
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-emerald-600 text-white text-sm rounded-xl hover:bg-emerald-700 transition font-medium flex items-center gap-2"
              >
                <Check className="w-4 h-4" />
                {editingAssignment ? 'ذخیره تغییرات' : 'ایجاد تخصیص'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
