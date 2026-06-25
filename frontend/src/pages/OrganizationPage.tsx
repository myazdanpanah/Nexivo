import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { ArrowRight, Building2, FolderTree, Users, ChevronDown, ChevronRight, Plus, Pencil, Trash2, X, Check } from 'lucide-react'

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

interface Company {
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

const ROLE_LABELS: Record<string, string> = {
  ceo: 'مدیرعامل', finance: 'مالی', sales: 'فروش', admin: 'مدیر سیستم',
}

const ROLE_COLORS: Record<string, string> = {
  ceo: 'bg-purple-100 text-purple-700', finance: 'bg-blue-100 text-blue-700',
  sales: 'bg-emerald-100 text-emerald-700', admin: 'bg-amber-100 text-amber-700',
}

export default function OrganizationPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToast()

  const [tree, setTree] = useState<Company[]>([])
  const [users, setUsers] = useState<UserOption[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  // Modal states
  const [modalType, setModalType] = useState<'company' | 'division' | 'team' | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState({ name: '', description: '', manager: 0, company: 0, division: 0 })

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'ceo')) {
      navigate('/dashboards')
      return
    }
    fetchData()
  }, [user, navigate])

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
    setForm({
      name: item.name,
      description: item.description || '',
      manager: mgrUser?.id || 0,
      company: type === 'division' ? parentId || 0 : 0,
      division: type === 'team' ? parentId || 0 : 0,
    })
  }

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      toast('نام الزامی است', 'error')
      return
    }
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
    } catch {
      toast('خطا در ذخیره', 'error')
    }
  }

  const handleDelete = async (type: 'company' | 'division' | 'team', id: number, name: string) => {
    if (!window.confirm(`آیا از حذف «${name}» اطمینان دارید؟`)) return
    try {
      if (type === 'company') await api.delete(`/auth/companies/${id}/`)
      else if (type === 'division') await api.delete(`/auth/divisions/${id}/`)
      else await api.delete(`/auth/teams/${id}/`)
      toast('حذف شد', 'success')
      fetchData()
    } catch {
      toast('خطا در حذف', 'error')
    }
  }

  if (user?.role !== 'admin' && user?.role !== 'ceo') return null

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboards" className="p-2 text-gray-400 hover:text-gray-600 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center">
                <FolderTree className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">ساختار سازمانی</h1>
                <p className="text-xs text-gray-500">شرکت → واحد → تیم → کارمند</p>
              </div>
            </div>
          </div>
          <button onClick={() => openCreate('company')} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm font-medium">
            <Building2 className="w-4 h-4" />
            شرکت جدید
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center"><Building2 className="w-5 h-5 text-indigo-600" /></div>
              <div><p className="text-2xl font-bold text-gray-900">{tree.length}</p><p className="text-xs text-gray-500">شرکت</p></div>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center"><FolderTree className="w-5 h-5 text-blue-600" /></div>
              <div><p className="text-2xl font-bold text-gray-900">{tree.reduce((s, c) => s + c.divisions.length, 0)}</p><p className="text-xs text-gray-500">واحد</p></div>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center"><Users className="w-5 h-5 text-emerald-600" /></div>
              <div><p className="text-2xl font-bold text-gray-900">{tree.reduce((s, c) => s + c.divisions.reduce((s2, d) => s2 + d.teams.reduce((s3, t) => s3 + t.member_count, 0), 0), 0)}</p><p className="text-xs text-gray-500">تیم</p></div>
            </div>
          </div>
        </div>

        {/* Tree View */}
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-bold text-gray-900">درخت سازمانی</h2>
          </div>

          {loading ? (
            <div className="p-12 text-center text-gray-500">در حال بارگذاری...</div>
          ) : tree.length === 0 ? (
            <div className="p-12 text-center">
              <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 mb-4">هنوز شرکتی تعریف نشده</p>
              <button onClick={() => openCreate('company')} className="px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm font-medium">ایجاد اولین شرکت</button>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {tree.map((company) => {
                const compKey = `c${company.id}`
                const isCompOpen = expanded[compKey] !== false
                return (
                  <div key={company.id}>
                    {/* Company row */}
                    <div className="px-6 py-4 hover:bg-gray-50 transition flex items-center justify-between">
                      <div className="flex items-center gap-3 cursor-pointer" onClick={() => toggle(compKey)}>
                        {isCompOpen ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                        <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center"><Building2 className="w-4 h-4 text-indigo-600" /></div>
                        <div>
                          <p className="text-sm font-bold text-gray-900">{company.name}</p>
                          <p className="text-xs text-gray-500">{company.divisions.length} واحد · {company.employees.length} کارمند مستقیم</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button onClick={() => openCreate('division', company.id)} className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded-lg transition" title="افزودن واحد"><Plus className="w-4 h-4" /></button>
                        <button onClick={() => openEdit('company', company)} className="p-1.5 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded-lg transition" title="ویرایش"><Pencil className="w-4 h-4" /></button>
                        <button onClick={() => handleDelete('company', company.id, company.name)} className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition" title="حذف"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    </div>

                    {/* Divisions */}
                    {isCompOpen && (
                      <div className="mr-8">
                        {company.divisions.map((div) => {
                          const divKey = `d${div.id}`
                          const isDivOpen = expanded[divKey] === true
                          return (
                            <div key={div.id}>
                              <div className="px-6 py-3 hover:bg-gray-50 transition flex items-center justify-between border-r-2 border-indigo-100">
                                <div className="flex items-center gap-3 cursor-pointer" onClick={() => toggle(divKey)}>
                                  {isDivOpen ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />}
                                  <div className="w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center"><FolderTree className="w-3.5 h-3.5 text-blue-600" /></div>
                                  <div>
                                    <p className="text-sm font-medium text-gray-800">{div.name}</p>
                                    <p className="text-[11px] text-gray-500">{div.manager_name ? `مدیر: ${div.manager_name}` : 'بدون مدیر'} · {div.teams.length} تیم · {div.employees.length} کارمند</p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-1">
                                  <button onClick={() => openCreate('team', div.id)} className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded transition" title="افزودن تیم"><Plus className="w-3.5 h-3.5" /></button>
                                  <button onClick={() => openEdit('division', div, company.id)} className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded transition"><Pencil className="w-3.5 h-3.5" /></button>
                                  <button onClick={() => handleDelete('division', div.id, div.name)} className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition"><Trash2 className="w-3.5 h-3.5" /></button>
                                </div>
                              </div>

                              {/* Teams */}
                              {isDivOpen && (
                                <div className="mr-8">
                                  {div.teams.map((team) => {
                                    const teamKey = `t${team.id}`
                                    const isTeamOpen = expanded[teamKey] === true
                                    return (
                                      <div key={team.id}>
                                        <div className="px-6 py-2 hover:bg-gray-50 transition flex items-center justify-between border-r-2 border-blue-100">
                                          <div className="flex items-center gap-3 cursor-pointer" onClick={() => toggle(teamKey)}>
                                            {isTeamOpen ? <ChevronDown className="w-3 h-3 text-gray-400" /> : <ChevronRight className="w-3 h-3 text-gray-400" />}
                                            <Users className="w-3.5 h-3.5 text-emerald-500" />
                                            <div>
                                              <p className="text-xs font-medium text-gray-700">{team.name}</p>
                                              <p className="text-[10px] text-gray-500">{team.manager_name ? `سرپرست: ${team.manager_name}` : 'بدون سرپرست'} · {team.member_count} عضو</p>
                                            </div>
                                          </div>
                                          <div className="flex items-center gap-1">
                                            <button onClick={() => openEdit('team', team, div.id)} className="p-0.5 text-gray-400 hover:text-emerald-500 hover:bg-emerald-50 rounded transition"><Pencil className="w-3 h-3" /></button>
                                            <button onClick={() => handleDelete('team', team.id, team.name)} className="p-0.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition"><Trash2 className="w-3 h-3" /></button>
                                          </div>
                                        </div>

                                        {/* Members */}
                                        {isTeamOpen && (
                                          <div className="mr-8 mb-1 border-r-2 border-emerald-100">
                                            {team.members.length === 0 ? (
                                              <p className="px-6 py-1 text-[10px] text-gray-400 italic">بدون عضو</p>
                                            ) : (
                                              team.members.map((m) => (
                                                <div key={m.id} className="px-6 py-1 flex items-center gap-2">
                                                  <div className="w-5 h-5 bg-gray-100 rounded-full flex items-center justify-center text-[9px] font-bold text-gray-600">{m.name.charAt(0)}</div>
                                                  <span className="text-[11px] text-gray-600">{m.name}</span>
                                                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${ROLE_COLORS[m.role] || 'bg-gray-100 text-gray-600'}`}>{ROLE_LABELS[m.role] || m.role}</span>
                                                </div>
                                              ))
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    )
                                  })}
                                  {/* Division-level employees */}
                                  {div.employees.length > 0 && (
                                    <div className="mr-8 mb-1 border-r-2 border-blue-100">
                                      <p className="px-6 py-1 text-[10px] text-gray-400 font-medium">کارمندان واحد:</p>
                                      {div.employees.map((e) => (
                                        <div key={e.id} className="px-6 py-1 flex items-center gap-2">
                                          <div className="w-5 h-5 bg-gray-100 rounded-full flex items-center justify-center text-[9px] font-bold text-gray-600">{e.name.charAt(0)}</div>
                                          <span className="text-[11px] text-gray-600">{e.name}</span>
                                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${ROLE_COLORS[e.role] || 'bg-gray-100 text-gray-600'}`}>{ROLE_LABELS[e.role] || e.role}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )
                        })}
                        {/* Company-level employees */}
                        {company.employees.length > 0 && (
                          <div className="px-6 py-2 border-r-2 border-indigo-100">
                            <p className="text-[10px] text-gray-400 font-medium mb-1">کارمندان مستقیم شرکت:</p>
                            <div className="flex flex-wrap gap-2">
                              {company.employees.map((e) => (
                                <span key={e.id} className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-[10px] text-gray-600">
                                  {e.name} <span className={`px-1 rounded text-[8px] ${ROLE_COLORS[e.role] || 'bg-gray-200'}`}>{ROLE_LABELS[e.role] || e.role}</span>
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>

      {/* Create/Edit Modal */}
      {modalType && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" dir="rtl">
          <div className="absolute inset-0 bg-black/40" onClick={() => setModalType(null)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h3 className="font-bold text-gray-900">
                {editingId ? 'ویرایش' : 'ایجاد'} {modalType === 'company' ? 'شرکت' : modalType === 'division' ? 'واحد' : 'تیم'}
              </h3>
              <button onClick={() => setModalType(null)} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">نام *</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">توضیحات</label>
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">مدیر</label>
                <select value={form.manager || ''} onChange={(e) => setForm({ ...form, manager: Number(e.target.value) })} className="w-full px-3 py-2.5 rounded-xl border border-gray-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none">
                  <option value="">انتخاب مدیر...</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>{u.first_name || u.last_name ? `${u.first_name} ${u.last_name}` : u.username} (@{u.username})</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3">
              <button onClick={() => setModalType(null)} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-xl transition">انصراف</button>
              <button onClick={handleSubmit} className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 transition font-medium flex items-center gap-2">
                <Check className="w-4 h-4" />
                {editingId ? 'ذخیره' : 'ایجاد'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
