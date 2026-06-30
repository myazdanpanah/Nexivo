import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Database, Table, Server, Plus, RefreshCw, Search, ChevronRight, HardDrive } from 'lucide-react'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { useAuthStore } from '../store/authStore'

interface DatabaseEntry {
  id: number
  source: string
  name: string
  table_name?: string
  type: 'dataset' | 'external'
  host?: string
  database?: string
  is_active: boolean
  row_count?: number
  column_count?: number
}

export default function DatabaseManagerPage() {
  const [databases, setDatabases] = useState<DatabaseEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const { toast } = useToast()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin' || user?.role === 'ceo'

  useEffect(() => {
    loadDatabases()
  }, [])

  const loadDatabases = async () => {
    setLoading(true)
    try {
      const res = await api.get('/db-manager/databases/')
      setDatabases(res.data)
    } catch {
      toast('خطا در بارگذاری پایگاه‌داده‌ها', 'error')
    } finally {
      setLoading(false)
    }
  }

  const filtered = databases.filter(
    (d) =>
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      (d.table_name && d.table_name.toLowerCase().includes(search.toLowerCase())) ||
      (d.host && d.host.toLowerCase().includes(search.toLowerCase()))
  )

  const localTables = filtered.filter((d) => d.source === 'local')
  const externalDbs = filtered.filter((d) => d.type === 'external')

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" dir="rtl">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/dashboards" className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
              <ChevronRight className="w-5 h-5" />
            </Link>
            <Database className="w-6 h-6 text-indigo-600" />
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">مدیریت پایگاه‌داده</h1>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/db-manager/sql"
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              SQL Editor
            </Link>
            <Link
              to="/db-manager/syncs"
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              Google Sheets
            </Link>
            {isAdmin && (
              <Link
                to="/db-manager/connections"
                className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
              >
                <Server className="w-4 h-4" />
                اتصالات خارجی
              </Link>
            )}
            <Link
              to="/db-manager/import"
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              <Plus className="w-4 h-4" />
              وارد کردن فایل
            </Link>
          </div>
        </div>
      </header>

      {/* Search bar */}
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="relative">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="جستجو در جداول و پایگاه‌داده‌ها..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pr-10 pl-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
          />
          <button
            onClick={loadDatabases}
            className="absolute left-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-indigo-600 transition"
            title="بازخوانی"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 pb-8">
        {loading ? (
          <div className="text-center py-20">
            <RefreshCw className="w-8 h-8 text-gray-400 mx-auto animate-spin mb-3" />
            <p className="text-gray-500 dark:text-gray-400">در حال بارگذاری...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <Database className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              {search ? 'نتیجه‌ای یافت نشد' : 'پایگاه‌داده‌ای وجود ندارد'}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              فایلی وارد کنید یا اتصال خارجی اضافه کنید
            </p>
            <div className="flex items-center justify-center gap-3">
              <Link
                to="/db-manager/import"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm font-medium"
              >
                وارد کردن فایل
              </Link>
              {isAdmin && (
                <Link
                  to="/db-manager/connections"
                  className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition text-sm font-medium"
                >
                  افزودن اتصال خارجی
                </Link>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Local Tables (Nexivo datasets) */}
            {localTables.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <HardDrive className="w-5 h-5 text-indigo-600" />
                  <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                    جداول Nexivo
                  </h2>
                  <span className="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-xs font-medium">
                    {localTables.length}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {localTables.map((db) => (
                    <Link
                      key={db.source}
                      to={`/db-manager/table/${db.source}/${db.table_name}`}
                      className="group bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-600 transition"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Table className="w-5 h-5 text-indigo-500" />
                          <span className="text-sm font-bold text-gray-900 dark:text-gray-100 group-hover:text-indigo-600 transition">
                            {db.name}
                          </span>
                        </div>
                      </div>
                      <div className="space-y-1.5 text-xs text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                            {db.table_name}
                          </span>
                        </div>
                        {db.row_count !== undefined && (
                          <div>{db.row_count.toLocaleString()} ردیف · {db.column_count} ستون</div>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {/* External Databases */}
            {externalDbs.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Server className="w-5 h-5 text-emerald-600" />
                  <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                    پایگاه‌داده‌های خارجی
                  </h2>
                  <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-full text-xs font-medium">
                    {externalDbs.length}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {externalDbs.map((db) => (
                    <ExternalDbCard key={db.source} db={db} />
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

function ExternalDbCard({ db }: { db: DatabaseEntry }) {
  const [tables, setTables] = useState<string[]>([])
  const [expanded, setExpanded] = useState(false)
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const loadTables = async () => {
    if (expanded) { setExpanded(false); return }
    setLoading(true)
    try {
      const res = await api.get(`/db-manager/databases/${db.source}/tables/`)
      setTables(res.data)
      setExpanded(true)
    } catch {
      toast('خطا در بارگذاری جداول', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <button
        onClick={loadTables}
        className="w-full p-5 text-right hover:bg-gray-50 dark:hover:bg-gray-750 transition"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-emerald-500" />
            <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{db.name}</span>
          </div>
          {loading ? (
            <RefreshCw className="w-4 h-4 text-gray-400 animate-spin" />
          ) : (
            <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? 'rotate-90' : ''}`} />
          )}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
          <div className="font-mono">{db.host}</div>
          <div>{db.database}</div>
        </div>
      </button>
      {expanded && tables.length > 0 && (
        <div className="border-t border-gray-100 dark:border-gray-700 px-5 py-3 max-h-60 overflow-y-auto space-y-1">
          {tables.map((t) => (
            <Link
              key={t}
              to={`/db-manager/table/${db.source}/${t}`}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition"
            >
              {t}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
