import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Server, Plus, Trash2, RefreshCw, PlugZap, Edit3 } from 'lucide-react'
import api from '../api/client'
import { useToast } from '../components/Toast'

interface ExternalDb {
  id: number
  name: string
  host: string
  port: number
  database: string
  username: string
  is_active: boolean
  created_at: string
}

const EMPTY_FORM = { name: '', host: '', port: 5432, database: '', username: '', password: '' }

export default function ExternalDbPage() {
  const [dbs, setDbs] = useState<ExternalDb[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [testingId, setTestingId] = useState<number | null>(null)
  const [testResult, setTestResult] = useState<{ id: number; ok: boolean; message: string } | null>(null)
  const { toast } = useToast()

  useEffect(() => { loadDbs() }, [])

  const loadDbs = async () => {
    setLoading(true)
    try {
      const res = await api.get('/db-manager/databases/')
      setDbs(res.data.filter((d: { type: string }) => d.type === 'external'))
    } catch {
      toast('خطا در بارگذاری اتصالات', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      const payload = { ...form, port: Number(form.port) }
      if (editingId) {
        await api.put(`/db-manager/databases/${editingId}/`, payload)
        toast('اتصال به‌روزرسانی شد', 'success')
      } else {
        await api.post('/db-manager/databases/', payload)
        toast('اتصال اضافه شد', 'success')
      }
      setForm(EMPTY_FORM)
      setEditingId(null)
      setShowForm(false)
      loadDbs()
    } catch {
      toast('خطا در ذخیره اتصال', 'error')
    }
  }

  const handleTest = async (id: number) => {
    setTestingId(id)
    setTestResult(null)
    try {
      const res = await api.post(`/db-manager/databases/${id}/test/`)
      setTestResult({ id, ok: res.data.ok, message: res.data.message })
    } catch {
      setTestResult({ id, ok: false, message: 'خطا در تست اتصال' })
    } finally {
      setTestingId(null)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('آیا از حذف این اتصال اطمینان دارید؟')) return
    try {
      await api.delete(`/db-manager/databases/${id}/`)
      toast('اتصال حذف شد', 'success')
      loadDbs()
    } catch {
      toast('خطا در حذف اتصال', 'error')
    }
  }

  const startEdit = (db: ExternalDb) => {
    setForm({ name: db.name, host: db.host, port: db.port, database: db.database, username: db.username, password: '' })
    setEditingId(db.id)
    setShowForm(true)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" dir="rtl">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/db-manager" className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Server className="w-5 h-5 text-emerald-600" />
            <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">اتصالات پایگاه‌داده خارجی</h1>
          </div>
          <button
            onClick={() => { setShowForm(!showForm); setEditingId(null); setForm(EMPTY_FORM) }}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition"
          >
            <Plus className="w-4 h-4" />
            افزودن اتصال
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-6 space-y-4">
        {/* Add/Edit form */}
        {showForm && (
          <div className="bg-white dark:bg-gray-800 border border-emerald-200 dark:border-emerald-700 rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100">
              {editingId ? 'ویرایش اتصال' : 'اتصال جدید'}
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <input placeholder="نام" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500" />
              <input placeholder="هاست" value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500" />
              <input placeholder="پورت" type="number" value={form.port} onChange={(e) => setForm({ ...form, port: parseInt(e.target.value) || 5432 })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500" />
              <input placeholder="نام دیتابیس" value={form.database} onChange={(e) => setForm({ ...form, database: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500" />
              <input placeholder="نام کاربری" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500" />
              <input placeholder="رمز عبور" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500" />
            </div>
            <div className="flex items-center gap-3">
              <button onClick={handleSave} className="px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition font-medium">
                {editingId ? 'ذخیره' : 'افزودن'}
              </button>
              <button onClick={() => { setShowForm(false); setEditingId(null) }} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 transition">
                انصراف
              </button>
            </div>
          </div>
        )}

        {/* Connection list */}
        {loading ? (
          <div className="text-center py-16">
            <RefreshCw className="w-6 h-6 text-gray-400 mx-auto animate-spin" />
          </div>
        ) : dbs.length === 0 ? (
          <div className="text-center py-16">
            <Server className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">اتصال خارجی وجود ندارد</p>
          </div>
        ) : (
          <div className="space-y-3">
            {dbs.map((db) => (
              <div key={db.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-emerald-500" />
                    <div>
                      <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{db.name}</span>
                      <span className={`mr-2 px-2 py-0.5 rounded-full text-[10px] font-medium ${db.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}`}>
                        {db.is_active ? 'فعال' : 'غیرفعال'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleTest(db.id)} disabled={testingId === db.id}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50">
                      {testingId === db.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <PlugZap className="w-3 h-3" />}
                      تست اتصال
                    </button>
                    <button onClick={() => startEdit(db)} className="p-1.5 text-gray-400 hover:text-indigo-600 transition">
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDelete(db.id)} className="p-1.5 text-gray-400 hover:text-red-600 transition">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 font-mono">
                  <span>{db.host}:{db.port}</span>
                  <span>/</span>
                  <span>{db.database}</span>
                  <span>/</span>
                  <span>{db.username}</span>
                </div>
                {testResult && testResult.id === db.id && (
                  <div className={`mt-3 text-xs px-3 py-2 rounded-lg ${testResult.ok ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300' : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'}`}>
                    {testResult.ok ? '✅' : '❌'} {testResult.message}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
