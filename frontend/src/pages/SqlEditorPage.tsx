import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Play, RefreshCw, Copy, Download } from 'lucide-react'
import CodeMirror from '@uiw/react-codemirror'
import { sql } from '@codemirror/lang-sql'
import { oneDark } from '@codemirror/theme-one-dark'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { useAuthStore } from '../store/authStore'

export default function SqlEditorPage() {
  const [sqlText, setSqlText] = useState('')
  const [source, setSource] = useState('local')
  const [result, setResult] = useState<{
    columns?: string[]
    data?: Record<string, unknown>[]
    row_count?: number
    rows_affected?: number
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<string[]>([])
  const { toast } = useToast()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin' || user?.role === 'ceo'

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center" dir="rtl">
        <div className="text-center">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">دسترسی غیرمجاز</h2>
          <p className="text-gray-500 dark:text-gray-400">فقط مدیر سیستم و مدیرعامل به SQL Editor دسترسی دارند</p>
        </div>
      </div>
    )
  }

  const executeQuery = async () => {
    if (!sqlText.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.post('/db-manager/sql/', { source, sql: sqlText.trim() })
      setResult(res.data)
      setHistory((prev) => [sqlText, ...prev.slice(0, 19)])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'خطا در اجرای کوئری'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const exportCsv = () => {
    if (!result?.data || !result?.columns) return
    const header = result.columns.join(',')
    const rows = result.data.map((row) => result.columns!.map((c) => String(row[c] ?? '')).join(',')).join('\n')
    const blob = new Blob([header + '\n' + rows], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'query-result.csv'
    a.click()
    URL.revokeObjectURL(url)
    toast('CSV دانلود شد', 'success')
  }

  const copyToClipboard = () => {
    if (!result?.data || !result?.columns) return
    const header = result.columns.join('\t')
    const rows = result.data.map((row) => result.columns!.map((c) => String(row[c] ?? '')).join('\t')).join('\n')
    navigator.clipboard.writeText(header + '\n' + rows)
    toast('در کلیپبورد کپی شد', 'success')
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col" dir="rtl">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="max-w-full mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/db-manager" className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">SQL Editor</h1>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="local">Nexivo (local)</option>
            </select>
            <button
              onClick={executeQuery}
              disabled={loading || !sqlText.trim()}
              className="flex items-center gap-2 px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              اجرا
            </button>
          </div>
        </div>
      </header>

      {/* Editor */}
      <div className="flex-1 flex flex-col p-6 gap-4 overflow-hidden">
        <div className="bg-gray-900 dark:bg-gray-950 border border-gray-700 rounded-xl overflow-hidden" style={{ minHeight: '200px' }}>
          <CodeMirror
            value={sqlText}
            onChange={(val) => setSqlText(val)}
            extensions={[sql()]}
            theme={oneDark}
            height="200px"
            basicSetup={{
              lineNumbers: true,
              highlightActiveLineGutter: true,
              highlightActiveLine: true,
              foldGutter: true,
              autocompletion: true,
            }}
            placeholder="SELECT * FROM table_name LIMIT 100;"
          />
        </div>

        {/* Results */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
            <p className="text-sm text-red-700 dark:text-red-300 font-mono">{error}</p>
          </div>
        )}

        {result && (
          <div className="flex-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden flex flex-col">
            {/* Result header */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {result.columns
                  ? `${result.row_count} ردیف · ${result.columns.length} ستون`
                  : `${result.rows_affected} ردیف تأثیر یافت`
                }
              </div>
              {result.columns && (
                <div className="flex items-center gap-2">
                  <button onClick={copyToClipboard} className="p-1.5 text-gray-400 hover:text-indigo-600 transition" title="کپی">
                    <Copy className="w-4 h-4" />
                  </button>
                  <button onClick={exportCsv} className="p-1.5 text-gray-400 hover:text-indigo-600 transition" title="خروجی CSV">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Result table */}
            {result.columns && result.data && (
              <div className="flex-1 overflow-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
                    <tr>
                      {result.columns.map((col) => (
                        <th key={col} className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 whitespace-nowrap">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.data.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-750">
                        {result.columns!.map((col) => (
                          <td key={col} className="px-3 py-2 text-gray-700 dark:text-gray-300 whitespace-nowrap font-mono text-xs">
                            {row[col] === null ? <span className="text-gray-400 italic">NULL</span> : String(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Query history */}
        {history.length > 0 && !result && !error && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-3">تاریخچه کوئری</h3>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {history.map((h, i) => (
                <button
                  key={i}
                  onClick={() => setSqlText(h)}
                  className="block w-full text-right px-3 py-1.5 text-xs font-mono text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded transition truncate"
                >
                  {h}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
