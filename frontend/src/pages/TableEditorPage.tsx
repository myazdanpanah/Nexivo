import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowRight, RefreshCw, Settings, Download, ChevronLeft, ChevronRight } from 'lucide-react'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import api from '../api/client'
import { useToast } from '../components/Toast'

ModuleRegistry.registerModules([AllCommunityModule])

interface SchemaColumn {
  name: string
  type: string
  nullable: boolean
  default: string | null
  max_length: number | null
}

export default function TableEditorPage() {
  const { source, table } = useParams<{ source: string; table: string }>()
  const [rowData, setRowData] = useState<Record<string, unknown>[]>([])
  const [colDefs, setColDefs] = useState<Array<{ field: string; headerName: string; editable: boolean }>>([])
  const [schema, setSchema] = useState<SchemaColumn[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [pendingChanges, setPendingChanges] = useState<Array<Record<string, unknown>>>([])
  const { toast } = useToast()
  const pageSize = 100

  const loadData = useCallback(async () => {
    if (!source || !table) return
    setLoading(true)
    try {
      const [dataRes, schemaRes, countRes] = await Promise.all([
        api.get(`/db-manager/tables/${source}/${table}/data/`, {
          params: { offset: page * pageSize, limit: pageSize },
        }),
        api.get(`/db-manager/tables/${source}/${table}/schema/`),
        api.get(`/db-manager/tables/${source}/${table}/count/`),
      ])
      setRowData(dataRes.data.rows)
      setSchema(schemaRes.data)
      setTotalCount(countRes.data.count)

      // Build column defs — use first column as row ID for editing
      const pkCol = schemaRes.data.length > 0 ? schemaRes.data[0].name : 'id'
      setColDefs(
        schemaRes.data.map((col: SchemaColumn) => ({
          field: col.name,
          headerName: col.name,
          editable: col.name !== pkCol, // PK is not editable
        }))
      )
    } catch {
      toast('خطا در بارگذاری داده‌ها', 'error')
    } finally {
      setLoading(false)
    }
  }, [source, table, page, toast])

  useEffect(() => { loadData() }, [loadData])

  const handleCellValueChanged = useCallback((event: { data: Record<string, unknown> }) => {
    setPendingChanges((prev) => {
      const pkCol = schema.length > 0 ? schema[0].name : 'id'
      const pkValue = event.data[pkCol]
      const existing = prev.findIndex((c) => c.pk_value === pkValue)
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = { ...updated[existing], ...event.data }
        return updated
      }
      return [...prev, { pk_column: pkCol, pk_value: pkValue, ...event.data }]
    })
  }, [schema])

  const saveChanges = async () => {
    if (!source || !table || pendingChanges.length === 0) return
    setSaving(true)
    try {
      // Build batch updates
      const pkCol = schema.length > 0 ? schema[0].name : 'id'
      const updates = pendingChanges.map((change) => ({
        pk_column: pkCol,
        pk_value: change[pkCol],
        column: Object.keys(change).find((k) => k !== 'pk_column' && k !== 'pk_value' && k !== pkCol),
        value: Object.values(change).find((_, i) => {
          const k = Object.keys(change)[i]
          return k !== 'pk_column' && k !== 'pk_value' && k !== pkCol
        }),
      })).filter((u) => u.column && u.value !== undefined)

      if (updates.length > 0) {
        await api.patch(`/db-manager/tables/${source}/${table}/batch/`, { updates })
      }
      setPendingChanges([])
      toast(`${updates.length} سلول ذخیره شد`, 'success')
      loadData()
    } catch {
      toast('خطا در ذخیره تغییرات', 'error')
    } finally {
      setSaving(false)
    }
  }

  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" dir="rtl">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="max-w-full mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/db-manager" className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">{table}</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {source === 'local' ? 'Nexivo' : 'خارجی'} · {totalCount.toLocaleString()} ردیف · {schema.length} ستون
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/db-manager/table/${source}/${table}/schema`}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              <Settings className="w-4 h-4" />
              اسکیما
            </Link>
            <Link
              to={`/db-manager/table/${source}/${table}/import`}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              <Download className="w-4 h-4" />
              وارد کردن
            </Link>
            {pendingChanges.length > 0 && (
              <button
                onClick={saveChanges}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium disabled:opacity-50"
              >
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
                ذخیره ({pendingChanges.length})
              </button>
            )}
            <button
              onClick={loadData}
              className="p-2 text-gray-400 hover:text-indigo-600 transition"
              title="بازخوانی"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* AG Grid */}
      <div className="p-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
          <div className="ag-theme-alpine" style={{ height: 'calc(100vh - 220px)', width: '100%' }}>
            <AgGridReact
              rowData={rowData}
              columnDefs={colDefs}
              defaultColDef={{
                sortable: true,
                filter: true,
                resizable: true,
                flex: 1,
                minWidth: 100,
              }}
              onCellValueChanged={handleCellValueChanged}
              animateRows={true}
              rowSelection="multiple"
              suppressRowClickSelection={true}
              enableCellTextSelection={true}
              loading={loading}
              pagination={false}
              getRowId={(params) => {
                const pkCol = schema.length > 0 ? schema[0].name : 'id'
                return String(params.data[pkCol] ?? Math.random())
              }}
            />
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              صفحه {page + 1} از {totalPages} · {totalCount.toLocaleString()} ردیف
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 text-gray-400 hover:text-indigo-600 disabled:opacity-30 disabled:cursor-not-allowed transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-700 dark:text-gray-300 px-2">{page + 1}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 text-gray-400 hover:text-indigo-600 disabled:opacity-30 disabled:cursor-not-allowed transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
