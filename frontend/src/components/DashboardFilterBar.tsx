import { useState, useEffect, useCallback, useRef } from 'react'
import { useDashboardStore, controlFiltersToQuery, type DashboardFilterControl } from '../store/dashboardStore'
import { X, Plus, Filter, ChevronDown, ChevronUp, Calendar, Search, CheckSquare, Sliders, Trash2, Shield } from 'lucide-react'
import api from '../api/client'
import { useAuthStore } from '../store/authStore'

interface Dataset {
  id: number
  name: string
  column_names: string[]
  column_types: Record<string, string>
}

const CONTROL_TYPES = [
  { value: 'dropdown', label: 'لیست کشویی', icon: ChevronDown },
  { value: 'date_range', label: 'محدوده تاریخ', icon: Calendar },
  { value: 'text_search', label: 'جستجوی متن', icon: Search },
  { value: 'checkbox', label: 'چک‌باکس', icon: CheckSquare },
  { value: 'slider', label: 'اسلایدر', icon: Sliders },
] as const

const FILTER_ROLE_OPTIONS = [
  { value: 'ceo', label: 'مدیرعامل' },
  { value: 'finance', label: 'مالی' },
  { value: 'sales', label: 'فروش' },
  { value: 'admin', label: 'مدیر سیستم' },
]

function generateId(): string {
  return `fc_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

export default function DashboardFilterBar() {
  const {
    filterControls,
    setFilterControls,
    addFilterControl,
    updateFilterControl,
    removeFilterControl,
    clearFilters,
    filters,
    removeFilter,
    widgets,
    pages,
  } = useDashboardStore()

  const dashboardId = useDashboardStore((s) => s.dashboardId)
  const activePageId = useDashboardStore((s) => s.activePageId)
  const updatePage = useDashboardStore((s) => s.updatePage)
  const hasLoadedRef = useRef(false)
  const lastPersistedRef = useRef('')
  const [expanded, setExpanded] = useState(true)
  const [addingControl, setAddingControl] = useState(false)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [newControlCol, setNewControlCol] = useState('')
  const [newControlType, setNewControlType] = useState<DashboardFilterControl['type']>('dropdown')
  const [newControlLabel, setNewControlLabel] = useState('')
  const [newControlDatasetId, setNewControlDatasetId] = useState<number | null>(null)
  const [newControlRoles, setNewControlRoles] = useState<string[]>([])
  const [editingFilterRoles, setEditingFilterRoles] = useState<string | null>(null)
  const editingFilterRef = useRef<HTMLDivElement>(null)

  // Close filter role popover on outside click
  useEffect(() => {
    if (!editingFilterRoles) return
    const handler = (e: MouseEvent) => {
      if (editingFilterRef.current && !editingFilterRef.current.contains(e.target as Node)) {
        setEditingFilterRoles(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [editingFilterRoles])

  // Get unique dataset IDs from widgets — prefer the active page's widgets
  // (top-level `widgets` stays empty for dashboards that use pages).
  const activePageWidgets = pages.find((p) => p.id === activePageId)?.widgets || widgets
  const datasetIds = [...new Set(activePageWidgets.map((w) => w.datasetId).filter(Boolean))] as number[]

  useEffect(() => {
    fetchDatasets()
  }, [])

  // Persist filter controls to backend on user edits (skip initial mount and page switches)
  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true
      return
    }
    const json = JSON.stringify(filterControls)
    if (json === lastPersistedRef.current) return // Skip redundant PUTs (e.g. from page switches)
    lastPersistedRef.current = json
    if (activePageId) {
      updatePage(activePageId, { filterControls: [...filterControls] })
    }
    if (dashboardId && activePageId) {
      api.put(`/dashboards/${dashboardId}/pages/${activePageId}/`, {
        filter_controls: filterControls,
      }).catch(() => {})
    }
  }, [filterControls, dashboardId, activePageId, updatePage])

  const fetchDatasets = async () => {
    try {
      const res = await api.get('/datasets/')
      setDatasets(res.data as Dataset[])
    } catch {
      // ignore
    }
  }

  // Fetch unique values for dropdown/checkbox controls
  const fetchUniqueValues = useCallback(async (datasetId: number, col: string): Promise<string[]> => {
    try {
      const res = await api.post(`/datasets/${datasetId}/query/`, {
        columns: [col],
        metrics: {},
      })
      const rows = res.data.data as Record<string, unknown>[]
      const uniqueVals = [...new Set(rows.map((r) => String(r[col] ?? '')))]
      return uniqueVals.sort()
    } catch {
      return []
    }
  }, [])

  // Fetch min/max for slider controls
  const fetchNumericRange = useCallback(async (datasetId: number, col: string): Promise<{ min: number; max: number }> => {
    try {
      const res = await api.post(`/datasets/${datasetId}/query/`, {
        columns: [col],
        metrics: { [col]: 'MIN' },
      })
      const min = Number(res.data.data[0]?.[col]) || 0
      const resMax = await api.post(`/datasets/${datasetId}/query/`, {
        columns: [col],
        metrics: { [col]: 'MAX' },
      })
      const max = Number(resMax.data.data[0]?.[col]) || 100
      return { min, max }
    } catch {
      return { min: 0, max: 100 }
    }
  }, [])

  const handleAddControl = async () => {
    if (!newControlCol || !newControlDatasetId) return

    const ds = datasets.find((d) => d.id === newControlDatasetId)
    const colType = (ds?.column_types[newControlCol] || '').toUpperCase()
    const isDate = colType.includes('TIMESTAMP') || colType.includes('DATE') || colType.includes('TIME')
    const isNumeric = ['BIGINT', 'INTEGER', 'SMALLINT', 'DOUBLE PRECISION', 'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT', 'INT64', 'FLOAT64'].includes(colType)

    // Auto-select type based on column type
    let autoType = newControlType
    if (isDate) autoType = 'date_range'
    else if (isNumeric) autoType = 'slider'

    const control: DashboardFilterControl = {
      id: generateId(),
      col: newControlCol,
      type: autoType,
      label: newControlLabel || newControlCol,
      datasetId: newControlDatasetId,
      value: null,
    }

    // Pre-fetch options for dropdown/checkbox
    if (autoType === 'dropdown' || autoType === 'checkbox') {
      const options = await fetchUniqueValues(newControlDatasetId, newControlCol)
      control.options = options
      if (autoType === 'checkbox') {
        control.multiSelect = true
      }
    }

    // Pre-fetch range for slider
    if (autoType === 'slider') {
      const range = await fetchNumericRange(newControlDatasetId, newControlCol)
      control.min = range.min
      control.max = range.max
      control.step = Math.max(1, Math.round((range.max - range.min) / 100))
      control.value = [range.min, range.max]
    }

    // Apply selected role restrictions to the new filter control
    if (newControlRoles.length > 0) {
      control.allowedRoles = newControlRoles
    }

    addFilterControl(control)
    setAddingControl(false)
    setNewControlCol('')
    setNewControlType('dropdown')
    setNewControlLabel('')
    setNewControlDatasetId(null)
    setNewControlRoles([])
  }

  const handleControlValueChange = (controlId: string, value: string | number | string[] | [number, number] | null) => {
    updateFilterControl(controlId, { value: value as DashboardFilterControl['value'] })
  }

  // Compute active control filters using shared utility
  const activeControlFilters = controlFiltersToQuery(filterControls)

  // Find which dataset to show columns for
  const selectedDs = newControlDatasetId ? datasets.find((d) => d.id === newControlDatasetId) : null
  const dsForNewControl = selectedDs || (datasets.find((d) => datasetIds.includes(d.id)))

  // Enforce filter-level access: only show controls the current user's role has access to
  const userRole = useAuthStore((s) => s.user?.role)
  const visibleControls = filterControls.filter((c) => {
    if (!c.allowedRoles || c.allowedRoles.length === 0) return true
    if (!userRole) return false
    return c.allowedRoles.includes(userRole)
  })

  const hasActiveFilters = activeControlFilters.length > 0 || filters.length > 0

  return (
    <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700" dir="rtl">
      {/* Filter bar header */}
      <div className="flex items-center justify-between px-6 py-2">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          <span className="text-sm font-medium text-gray-600 dark:text-gray-300">فیلترها</span>
          {hasActiveFilters && (
            <span className="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 text-[10px] rounded-full font-medium">
              {activeControlFilters.length + filters.length} فعال
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {(hasActiveFilters) && (
            <button
              onClick={() => {
                // Clear all control values
                setFilterControls(filterControls.map((c) => ({ ...c, value: null })))
                clearFilters()
              }}
              className="text-xs text-gray-500 dark:text-gray-400 hover:text-red-500 transition"
            >
              پاک کردن همه
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Active filter chips */}
      {hasActiveFilters && !expanded && (
        <div className="flex flex-wrap gap-1.5 px-6 pb-2">
          {filterControls
            .filter((c) => c.value !== null && c.value !== '' && c.value !== undefined)
            .map((c) => (
              <span
                key={c.id}
                className="flex items-center gap-1 px-2 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-xs border border-indigo-200 dark:border-indigo-700"
              >
                <span className="font-medium">{c.label}:</span>
                <span>
                  {c.type === 'slider' && Array.isArray(c.value)
                    ? `${c.value[0]} – ${c.value[1]}`
                    : c.type === 'checkbox' && Array.isArray(c.value)
                    ? c.value.join(', ')
                    : String(c.value)}
                </span>
                <button
                  onClick={() => handleControlValueChange(c.id, null)}
                  className="hover:text-indigo-900"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          {filters.map((f, idx) => (              <span
                key={idx}
                className="flex items-center gap-1 px-2 py-1 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-xs border border-amber-200 dark:border-amber-700"
              >
              <span className="font-medium">{f.col}:</span>
              <span>{String(f.val)}</span>
              <button
                onClick={() => removeFilter(f.col)}
                className="hover:text-amber-900"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Expanded controls */}
      {expanded && (
        <div className="px-6 pb-3">
          <div className="flex flex-wrap gap-3 items-end">
            {visibleControls.map((control) => (
                <div key={control.id} className="relative">
                  <FilterControlWidget
                    control={control}
                    onChange={(value) => handleControlValueChange(control.id, value)}
                  />
                  {/* Filter access indicator */}
                  {control.allowedRoles && control.allowedRoles.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center z-10" title={`فقط برای: ${control.allowedRoles.join(', ')}`}>
                      <Shield className="w-2 h-2" />
                    </span>
                  )}
                  <button
                    onClick={() => setEditingFilterRoles(editingFilterRoles === control.id ? null : control.id)}
                    className="absolute -top-1.5 left-6 w-4 h-4 bg-amber-100 hover:bg-amber-200 text-amber-600 rounded-full flex items-center justify-center text-[8px] transition z-10"
                    title="دسترسی فیلتر"
                  >
                    <Shield className="w-2 h-2" />
                  </button>
                  <button
                    onClick={() => removeFilterControl(control.id)}
                    className="absolute -top-1 -left-1 w-4 h-4 bg-gray-200 hover:bg-red-400 hover:text-white rounded-full flex items-center justify-center text-[8px] text-gray-500 transition z-10"
                    title="حذف فیلتر"
                  >
                    <Trash2 className="w-2 h-2" />
                  </button>
                  {/* Inline role picker for filter */}
                  {editingFilterRoles === control.id && (
                    <div ref={editingFilterRef} className="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg p-2 z-50 min-w-[140px]">
                      <div className="text-[10px] font-medium text-gray-600 dark:text-gray-300 mb-1">دسترسی فیلتر:</div>
                      {FILTER_ROLE_OPTIONS.map((r) => (
                        <label key={r.value} className="flex items-center gap-1.5 px-1 py-0.5 rounded hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={!control.allowedRoles || control.allowedRoles.length === 0 || control.allowedRoles.includes(r.value)}
                            onChange={(e) => {
                              const current = control.allowedRoles || []
                              const allRoles = FILTER_ROLE_OPTIONS.map((x) => x.value)
                              let newRoles: string[]
                              if (e.target.checked) {
                                newRoles = [...current, r.value]
                                if (newRoles.length === allRoles.length) newRoles = []
                              } else {
                                newRoles = current.filter((x) => x !== r.value)
                              }
                              updateFilterControl(control.id, { allowedRoles: newRoles })
                            }}
                            className="w-3 h-3 text-indigo-600 rounded border-gray-300 dark:border-gray-600 focus:ring-indigo-500"
                          />
                          <span className="text-[10px] text-gray-600 dark:text-gray-400">{r.label}</span>
                        </label>
                      ))}
                      <p className="text-[9px] text-gray-400 mt-1">بدون انتخاب = همه</p>
                    </div>
                  )}
                </div>
            ))}

            {/* Add control button */}
            {!addingControl ? (
              <button
                onClick={() => setAddingControl(true)}
                className="flex items-center gap-1.5 px-3 py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-sm text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition"
              >
                <Plus className="w-4 h-4" />
                افزودن فیلتر
              </button>
            ) : (
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl p-3 space-y-2 min-w-[280px]">
                <div className="text-xs font-medium text-gray-700 dark:text-gray-300">فیلتر جدید</div>

                {/* Dataset selector */}
                <select
                  value={newControlDatasetId || ''}
                  onChange={(e) => setNewControlDatasetId(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                >
                  <option value="">مجموعه داده...</option>
                  {datasets.filter((d) => datasetIds.includes(d.id)).map((ds) => (
                    <option key={ds.id} value={ds.id}>{ds.name}</option>
                  ))}
                </select>

                {/* Column selector */}
                {dsForNewControl && (
                  <select
                    value={newControlCol}
                    onChange={(e) => setNewControlCol(e.target.value)}
                    className="w-full px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                  >
                    <option value="">ستون...</option>
                    {dsForNewControl.column_names.map((col) => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                )}

                {/* Type selector */}
                <select
                  value={newControlType}
                  onChange={(e) => setNewControlType(e.target.value as DashboardFilterControl['type'])}
                  className="w-full px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                >
                  {CONTROL_TYPES.map((ct) => (
                    <option key={ct.value} value={ct.value}>{ct.label}</option>
                  ))}
                </select>

                {/* Label */}
                <input
                  type="text"
                  value={newControlLabel}
                  onChange={(e) => setNewControlLabel(e.target.value)}
                  placeholder="برچسب (اختیاری)"
                  className="w-full px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
                />

                {/* Filter access control */}
                <div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
                    <Shield className="w-2.5 h-2.5" />
                    دسترسی فیلتر (اختیاری)
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {FILTER_ROLE_OPTIONS.map((r) => (
                      <button
                        key={r.value}
                        type="button"
                        onClick={() => setNewControlRoles((prev) => prev.includes(r.value) ? prev.filter((v) => v !== r.value) : [...prev, r.value])}
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium border transition ${
                          newControlRoles.includes(r.value)
                            ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 border-indigo-300 dark:border-indigo-600'
                            : 'bg-gray-50 dark:bg-gray-700 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-600'
                        }`}
                      >
                        {r.label}
                      </button>
                    ))}
                  </div>
                  <p className="text-[9px] text-gray-400 mt-0.5">بدون انتخاب = همه</p>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleAddControl}
                    disabled={!newControlCol || !newControlDatasetId}
                    className="flex-1 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                  >
                    افزودن
                  </button>
                  <button
                    onClick={() => setAddingControl(false)}
                    className="px-3 py-1.5 text-gray-500 dark:text-gray-400 text-xs rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                  >
                    انصراف
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

/** Individual filter control widget */
function FilterControlWidget({
  control,
  onChange,
}: {
  control: DashboardFilterControl
  onChange: (value: string | number | string[] | [number, number] | null) => void
}) {
  if (control.type === 'dropdown') {
    return (
      <div className="min-w-[160px]">
        <label className="block text-[10px] text-gray-500 mb-0.5 font-medium">{control.label}</label>
        <div className="relative">
          <select
            value={String(control.value || '')}
            onChange={(e) => onChange(e.target.value || null)}
            className="w-full px-2 py-1.5 pr-6 rounded-lg border border-gray-300 dark:border-gray-600 text-xs bg-white dark:bg-gray-800 dark:text-gray-200 focus:ring-1 focus:ring-indigo-500 outline-none appearance-none"
          >
            <option value="">همه</option>
            {(control.options || []).map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
          <ChevronDown className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none" />
          {control.value && (
            <button
              onClick={() => onChange(null)}
              className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    )
  }

  if (control.type === 'date_range') {
    const val = control.value as [number, number] | null
    const startStr = val ? new Date(val[0]).toISOString().split('T')[0] : ''
    const endStr = val ? new Date(val[1]).toISOString().split('T')[0] : ''
    return (
      <div className="min-w-[240px]">
        <label className="block text-[10px] text-gray-500 mb-0.5 font-medium">{control.label}</label>
        <div className="flex items-center gap-1">
          <input
            type="date"
            value={startStr}
            onChange={(e) => {
              const start = e.target.value ? new Date(e.target.value).getTime() : null
              if (start !== null && val) onChange([start, val[1]])
              else if (start !== null) onChange([start, Date.now()])
            }}
            className="flex-1 px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
          />
          <span className="text-gray-400 text-xs">تا</span>
          <input
            type="date"
            value={endStr}
            onChange={(e) => {
              const end = e.target.value ? new Date(e.target.value).getTime() + 86400000 : null
              if (end !== null && val) onChange([val[0], end])
              else if (end !== null) onChange([0, end])
            }}
            className="flex-1 px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
          />
        </div>
      </div>
    )
  }

  if (control.type === 'text_search') {
    return (
      <div className="min-w-[160px]">
        <label className="block text-[10px] text-gray-500 mb-0.5 font-medium">{control.label}</label>
        <div className="relative">
          <Search className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none" />
          <input
            type="text"
            value={String(control.value || '')}
            onChange={(e) => onChange(e.target.value || null)}
            placeholder="جستجو..."
            className="w-full pr-7 pl-6 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
          />
          {control.value && (
            <button
              onClick={() => onChange(null)}
              className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    )
  }

  if (control.type === 'checkbox') {
    const selected = (control.value as string[] | null) || []
    return (
      <div className="min-w-[160px]">
        <label className="block text-[10px] text-gray-500 mb-0.5 font-medium">{control.label}</label>
        <div className="max-h-32 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg p-1.5 space-y-0.5">
          {(control.options || []).map((opt) => (
            <label key={opt} className="flex items-center gap-1.5 px-1 py-0.5 rounded hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(opt)}
                onChange={(e) => {
                  const next: string[] = e.target.checked
                    ? [...selected, opt]
                    : selected.filter((s) => s !== opt)
                  onChange(next.length > 0 ? (next as string[]) : null)
                }}
                className="w-3 h-3 text-indigo-600 rounded border-gray-300 dark:border-gray-600 focus:ring-indigo-500"
              />
              <span className="text-xs text-gray-700 dark:text-gray-300 truncate">{opt}</span>
            </label>
          ))}
        </div>
      </div>
    )
  }

  if (control.type === 'slider') {
    const val = control.value as [number, number] | null
    const min = control.min ?? 0
    const max = control.max ?? 100
    const currentMin = val ? val[0] : min
    const currentMax = val ? val[1] : max
    return (
      <div className="min-w-[200px]">
        <label className="block text-[10px] text-gray-500 mb-0.5 font-medium">
          {control.label}: {currentMin} – {currentMax}
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={currentMin}
            onChange={(e) => {
              const v = Number(e.target.value)
              onChange([v, currentMax])
            }}
            className="w-16 px-1.5 py-1 rounded border border-gray-300 dark:border-gray-600 text-xs text-center focus:ring-1 focus:ring-indigo-500 outline-none"
          />
          <input
            type="range"
            min={min}
            max={max}
            step={control.step || 1}
            value={currentMax}
            onChange={(e) => onChange([currentMin, Number(e.target.value)])}
            className="flex-1 accent-indigo-600"
          />
          <input
            type="number"
            value={currentMax}
            onChange={(e) => {
              const v = Number(e.target.value)
              onChange([currentMin, v])
            }}
            className="w-16 px-1.5 py-1 rounded border border-gray-300 dark:border-gray-600 text-xs text-center focus:ring-1 focus:ring-indigo-500 outline-none"
          />
        </div>
      </div>
    )
  }

  return null
}
