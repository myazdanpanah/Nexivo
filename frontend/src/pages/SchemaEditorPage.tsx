import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowRight, Plus, Trash2, RefreshCw, Pencil, Check, X } from 'lucide-react'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { useAuthStore } from '../store/authStore'

interface SchemaColumn {
  name: string
  type: string
  nullable: boolean
  default: string | null
  max_length: number | null
}

const PG_TYPES = [
  'TEXT', 'VARCHAR', 'INTEGER', 'BIGINT', 'SMALLINT',
  'DOUBLE PRECISION', 'REAL', 'NUMERIC', 'BOOLEAN',
  'DATE', 'TIMESTAMP', 'JSON', 'JSONB', 'UUID', 'BYTEA',
]

export default function SchemaEditorPage() {
  const { source, table } = useParams<{ source: string; table: string }>()
  const [schema, setSchema] = useState<SchemaColumn[]>([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [newCol, setNewCol] = useState({ name: '', type: 'TEXT', nullable: true, default: '' })
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [changingType, setChangingType] = useState<string | null>(null)
  const [typeValue, setTypeValue] = useState('TEXT')
  const { toast } = useToast()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin' || user?.role === 'ceo'

  useEffect(() => { loadSchema() }, [source, table])

  const loadSchema = async () => {
    if (!source || !table) return
    setLoading(true)
    try {
      const res = await api.get(`/db-manager/tables/${source}/${table}/schema/`)
      setSchema(res.data)
    } catch {
      toast('خطا در بارگذاری اسکیما', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async () => {
    if (!source || !table || !newCol.name.trim()) return
    try {
      await api.post(`/db-manager/tables/${source}/${table}/columns/`, {
        column_name: newCol.name.trim(),
        column_type: newCol.type,
        nullable: newCol.nullable,
        default: newCol.default || undefined,
      })
      setShowAdd(false)
      setNewCol({ name: '', type: 'TEXT', nullable: true, default: '' })
      toast('ستون اضافه شد', 'success')
      loadSchema()
    } catch {
      toast('خطا در افزودن ستون', 'error')
    }
  }

  const handleRename = async (oldName: string) => {
    if (!source || !table || !renameValue.trim()) return
    try {
      await api.patch(`/db-manager/tables/${source}/${table}/columns/${oldName}/`, {
        new_name: renameValue.trim(),
      })
      setRenaming(null)
      toast('نام ستون تغییر کرد', 'success')
      loadSchema()
    } catch {
      toast('خطا در تغییر نام', 'error')
    }
  }

  const handleChangeType = async (colName: string) => {
    if (!source || !table) return
    try {
      await api.patch(`/db-manager/tables/${source}/${table}/columns/${colName}/`, {
        new_type: typeValue,
      })
      setChangingType(null)
      toast('نوع ستون تغییر کرد', 'success')
      loadSchema()
    } catch {
      toast('خطا در تغییر نوع', 'error')
    }
  }

  const handleDrop = async (colName: string) => {
    if (!source || !table) return
    if (!window.confirm(`آیا از حذف ستون «${colName}» اطمینان دارید؟`)) return
    try {
      await api.delete(`/db-manager/tables/${source}/${table}/columns/${colName}/drop/`)
      toast('ستون حذف شد', 'success')
      loadSchema()
    } catch {
      toast('خطا در حذف ستون', 'error')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" dir="rtl">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to={`/db-manager/table/${source}/${table}`} className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">مدیریت اسکیما</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">{table} · {schema.length} ستون</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isAdmin && (
              <button
                onClick={() => setShowAdd(!showAdd)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                <Plus className="w-4 h-4" />
                افزودن ستون
              </button>
            )}
            <button onClick={loadSchema} className="p-2 text-gray-400 hover:text-indigo-600 transition">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-6">
        {/* Add column form */}
        {showAdd && (
          <div className="bg-white dark:bg-gray-800 border border-indigo-200 dark:border-indigo-700 rounded-xl p-5 mb-6">
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-4">ستون جدید</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <input
                placeholder="نام ستون"
                value={newCol.name}
                onChange={(e) => setNewCol({ ...newCol, name: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <select
                value={newCol.type}
                onChange={(e) => setNewCol({ ...newCol, type: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {PG_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <input
                placeholder="مقدار پیش‌فرض (اختیاری)"
                value={newCol.default}
                onChange={(e) => setNewCol({ ...newCol, default: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <div className="flex items-center gap-2">
                <button onClick={handleAdd} className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
                  افزودن
                </button>
                <button onClick={() => setShowAdd(false)} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 transition">
                  انصراف
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Schema table */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">نام</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">نوع</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">nullable</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">پیش‌فرض</th>
                {isAdmin && <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">عملیات</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">در حال بارگذاری...</td></tr>
              ) : schema.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">ستونی یافت نشد</td></tr>
              ) : (
                schema.map((col) => (
                  <tr key={col.name} className="border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-750 transition">
                    <td className="px-4 py-3">
                      {renaming === col.name ? (
                        <div className="flex items-center gap-1">
                          <input
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleRename(col.name); if (e.key === 'Escape') setRenaming(null) }}
                            autoFocus
                            className="px-2 py-1 text-sm border border-indigo-300 dark:border-indigo-600 dark:bg-gray-900 dark:text-gray-100 rounded outline-none"
                          />
                          <button onClick={() => handleRename(col.name)} className="text-green-600 hover:text-green-700"><Check className="w-4 h-4" /></button>
                          <button onClick={() => setRenaming(null)} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
                        </div>
                      ) : (
                        <span className="font-mono text-gray-900 dark:text-gray-100">{col.name}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {changingType === col.name ? (
                        <div className="flex items-center gap-1">
                          <select
                            value={typeValue}
                            onChange={(e) => setTypeValue(e.target.value)}
                            className="px-2 py-1 text-sm border border-indigo-300 dark:border-indigo-600 dark:bg-gray-900 dark:text-gray-100 rounded outline-none"
                          >
                            {PG_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                          </select>
                          <button onClick={() => handleChangeType(col.name)} className="text-green-600 hover:text-green-700"><Check className="w-4 h-4" /></button>
                          <button onClick={() => setChangingType(null)} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
                        </div>
                      ) : (
                        <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-gray-700 dark:text-gray-300">{col.type}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs ${col.nullable ? 'text-green-600' : 'text-red-500'}`}>
                        {col.nullable ? 'بله' : 'خیر'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 font-mono">
                      {col.default || '—'}
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => { setRenaming(col.name); setRenameValue(col.name) }}
                            className="p-1 text-gray-400 hover:text-indigo-600 transition"
                            title="تغییر نام"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => { setChangingType(col.name); setTypeValue(col.type) }}
                            className="p-1 text-gray-400 hover:text-amber-600 transition"
                            title="تغییر نوع"
                          >
                            <span className="text-[10px] font-mono">T</span>
                          </button>
                          <button
                            onClick={() => handleDrop(col.name)}
                            className="p-1 text-gray-400 hover:text-red-600 transition"
                            title="حذف ستون"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
