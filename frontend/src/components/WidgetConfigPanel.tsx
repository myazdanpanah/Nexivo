import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useDashboardStore } from '../store/dashboardStore'
import api from '../api/client'
import { X, BarChart3, PieChart, TrendingUp, Table, Hash, Circle, Target, GitBranch } from 'lucide-react'
import { formatKpiValue, DEFAULT_KPI_FORMAT, type KpiFormat } from '../utils/kpiFormat'

interface WidgetConfigPanelProps {
  widgetId: string
  onClose: () => void
}

const chartTypes = [
  { value: 'bar', label: 'میله‌ای', icon: BarChart3 },
  { value: 'stacked_bar', label: 'میله‌ای انباشته', icon: BarChart3 },
  { value: 'line', label: 'خطی', icon: TrendingUp },
  { value: 'area', label: 'سطحی', icon: TrendingUp },
  { value: 'pie', label: 'دایره‌ای', icon: PieChart },
  { value: 'donut', label: ' دونات', icon: Circle },
  { value: 'scatter', label: 'پراکنده', icon: Target },
  { value: 'gauge', label: 'گیج', icon: GitBranch },
  { value: 'table', label: 'جدول', icon: Table },
  { value: 'kpi', label: 'شاخص کلیدی', icon: Hash },
]

const AGG_OPTIONS = ['SUM', 'COUNT', 'AVG', 'MIN', 'MAX'] as const

const NUMERIC_TYPES = new Set([
  'BIGINT', 'INTEGER', 'SMALLINT', 'DOUBLE PRECISION',
  'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT',
  'INT64', 'FLOAT64',
])

interface Dataset {
  id: number
  name: string
  column_names: string[]
  column_types: Record<string, string>
}



export default function WidgetConfigPanel({ widgetId, onClose }: WidgetConfigPanelProps) {
  const { id: dashboardId } = useParams<{ id: string }>()
  const { widgets, updateWidget } = useDashboardStore()
  const widget = widgets.find((w) => w.id === widgetId)

  const [title, setTitle] = useState(widget?.title || '')
  const [chartType, setChartType] = useState(widget?.chartType || 'bar')
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(widget?.datasetId || null)
  const [selectedColumns, setSelectedColumns] = useState<string[]>(
    (widget?.queryConfig?.columns as string[]) || []
  )
  const [metrics, setMetrics] = useState<Record<string, string>>(
    (widget?.queryConfig?.metrics as Record<string, string>) || {}
  )
  // Date granularity: { col: 'month' }
  const [dateTruncs, setDateTruncs] = useState<Record<string, string>>(
    (widget?.queryConfig?.date_truncs as Record<string, string>) || {}
  )

  // KPI formatting state
  const savedKpiFormat = (widget?.chartConfig as Record<string, unknown>)?.kpiFormat as KpiFormat | undefined
  const [kpiFormat, setKpiFormat] = useState<KpiFormat>(savedKpiFormat || DEFAULT_KPI_FORMAT)

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId)

  useEffect(() => {
    fetchDatasets()
  }, [])

  // When dataset changes, auto-select all columns and auto-assign metrics from column types
  const prevDatasetIdRef = useRef<number | null>(selectedDatasetId)
  useEffect(() => {
    if (selectedDatasetId !== prevDatasetIdRef.current) {
      prevDatasetIdRef.current = selectedDatasetId
      if (selectedDataset) {
        setSelectedColumns(selectedDataset.column_names)
        if (chartType !== 'table') {
          const autoMetrics: Record<string, string> = {}
          for (const col of selectedDataset.column_names) {
            const pgType = (selectedDataset.column_types[col] || '').toUpperCase()
            if (NUMERIC_TYPES.has(pgType)) {
              autoMetrics[col] = 'SUM'
            }
          }
          setMetrics(autoMetrics)
        } else {
          setMetrics({})
        }
      } else {
        setSelectedColumns([])
        setMetrics({})
      }
    }
  }, [selectedDatasetId, selectedDataset, chartType])

  // When chart type changes to/from table, update metrics accordingly
  useEffect(() => {
    if (!selectedDataset) return
    if (chartType === 'table') {
      setMetrics({})
    } else {
      const autoMetrics: Record<string, string> = {}
      for (const col of selectedColumns) {
        const pgType = (selectedDataset.column_types[col] || '').toUpperCase()
        if (NUMERIC_TYPES.has(pgType)) {
          autoMetrics[col] = metrics[col] || 'SUM'
        }
      }
      setMetrics(autoMetrics)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartType])

  const fetchDatasets = async () => {
    try {
      const res = await api.get('/datasets/')
      setDatasets(res.data)
    } catch {
      // ignore
    }
  }

  const toggleColumn = (col: string) => {
    setSelectedColumns((prev) => (prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]))
  }

  const toggleMetric = (col: string) => {
    setMetrics((prev) => {
      const next = { ...prev }
      if (next[col]) {
        delete next[col] // metric → dimension
      } else {
        next[col] = 'SUM' // dimension → metric
      }
      return next
    })
  }

  const setAggFunc = (col: string, func: string) => {
    setMetrics((prev) => ({ ...prev, [col]: func }))
  }

  const isMetric = (col: string) => col in metrics

  const handleSave = async () => {
    if (!widget) return

    const queryConfig: Record<string, unknown> = {
      ...widget.queryConfig,
      columns: selectedColumns.length > 0 ? selectedColumns : undefined,
    }
    if (chartType !== 'table' && Object.keys(metrics).length > 0) {
      queryConfig.metrics = metrics
    } else {
      queryConfig.metrics = undefined
    }
    // Date truncs
    if (Object.keys(dateTruncs).length > 0) {
      queryConfig.date_truncs = dateTruncs
    } else {
      queryConfig.date_truncs = undefined
    }

    // Save KPI format in chartConfig
    const chartConfig: Record<string, unknown> = {
      ...widget.chartConfig,
    }
    if (chartType === 'kpi') {
      chartConfig.kpiFormat = kpiFormat
    }

    try {
      await api.put(`/dashboards/${dashboardId}/widgets/${widgetId}/`, {
        title,
        chart_type: chartType,
        dataset: selectedDatasetId,
        chart_config: chartConfig,
        query_config: queryConfig,
      })

      updateWidget(widgetId, {
        title,
        chartType,
        datasetId: selectedDatasetId,
        queryConfig,
        chartConfig,
      })

      onClose()
    } catch {
      // ignore
    }
  }

  if (!widget) return null

  return (
    <div className="fixed inset-0 z-50 flex" dir="rtl">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />

      {/* Panel */}
      <div className="absolute left-0 top-0 bottom-0 w-96 bg-white shadow-xl overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="font-bold text-gray-900">تنظیمات نمودار</h3>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">عنوان</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
              dir="rtl"
            />
          </div>

          {/* Chart Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">نوع نمودار</label>
            <div className="grid grid-cols-2 gap-2">
              {chartTypes.map((ct) => {
                const Icon = ct.icon
                return (
                  <button
                    key={ct.value}
                    onClick={() => setChartType(ct.value)}
                    className={`flex items-center gap-2 p-3 rounded-xl border-2 transition ${
                      chartType === ct.value
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-gray-200 hover:border-gray-300 text-gray-600'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{ct.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Dataset */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">مجموعه داده</label>
            <select
              value={selectedDatasetId || ''}
              onChange={(e) => setSelectedDatasetId(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            >
              <option value="">انتخاب کنید...</option>
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name} ({ds.column_names.length} ستون)
                </option>
              ))}
            </select>
          </div>

          {/* Column Picker with Dimension / Metric roles */}
          {selectedDataset && selectedDataset.column_names.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ستون\u200cها
                {chartType !== 'table' && (
                  <span className="text-xs text-gray-400 mr-2">
                    (روی برچسب کلیک کنید تا بین دسته/مقدار تغییر کند)
                  </span>
                )}
              </label>
              <div className="space-y-1.5 max-h-56 overflow-y-auto border border-gray-200 rounded-xl p-3">
                {selectedDataset.column_names.map((col) => {
                  const checked = selectedColumns.includes(col)
                  const metric = isMetric(col)
                  return (
                    <div
                      key={col}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-lg transition ${
                        checked ? 'bg-gray-50' : 'opacity-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleColumn(col)}
                        className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-700 flex-1">{col}</span>

                      {/* Role badge + agg picker (only for non-table charts) */}
                      {chartType !== 'table' && checked && (
                        <div className="flex items-center gap-1">
                          {metric ? (
                            <div className="flex items-center gap-0.5">
                              <select
                                value={metrics[col]}
                                onChange={(e) => setAggFunc(col, e.target.value)}
                                className="text-[10px] px-1 py-0.5 bg-amber-100 text-amber-700 rounded-full border-0 outline-none cursor-pointer font-medium"
                                title="تابع تجمیع"
                              >
                                {AGG_OPTIONS.map((f) => (
                                  <option key={f} value={f}>{f}</option>
                                ))}
                              </select>
                              <button
                                onClick={() => toggleMetric(col)}
                                className="text-[10px] w-3.5 h-3.5 flex items-center justify-center text-amber-500 hover:text-amber-700 hover:bg-amber-200 rounded-full transition"
                                title="تبدیل به دسته"
                              >
                                ×
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => toggleMetric(col)}
                              className="text-[10px] px-1.5 py-0.5 bg-indigo-100 text-indigo-600 rounded-full hover:bg-indigo-200 transition font-medium"
                              title="تبدیل به مقدار"
                            >
                              دسته
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              <div className="flex items-center gap-2 mt-2">
                <button
                  onClick={() => setSelectedColumns(selectedDataset.column_names)}
                  className="text-xs text-indigo-600 hover:text-indigo-700"
                >
                  انتخاب همه
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={() => {
                    setSelectedColumns([])
                    setMetrics({})
                    setDateTruncs({})
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  حذف انتخاب
                </button>
              </div>
            </div>
          )}

          {/* Date Granularity Picker */}
          {selectedDataset && chartType !== 'table' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                گروه‌بندی تاریخ
                <span className="text-xs text-gray-400 mr-2">
                  (ستون‌های تاریخی را خودکار گروه‌بندی کنید)
                </span>
              </label>
              <div className="space-y-1.5">
                {selectedDataset.column_names
                  .filter((col) => {
                    const pgType = (selectedDataset.column_types[col] || '').toUpperCase()
                    return pgType.includes('TIMESTAMP') || pgType.includes('DATE') || pgType.includes('TIME')
                  })
                  .map((col) => (
                    <div key={col} className="flex items-center gap-2 px-2 py-1.5 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-700 flex-1">{col}</span>
                      <select
                        value={dateTruncs[col] || ''}
                        onChange={(e) => {
                          setDateTruncs((prev) => {
                            const next = { ...prev }
                            if (e.target.value) {
                              next[col] = e.target.value
                            } else {
                              delete next[col]
                            }
                            return next
                          })
                        }}
                        className="text-xs px-2 py-1 rounded-lg border border-gray-300 focus:ring-1 focus:ring-indigo-500 outline-none"
                      >
                        <option value="">بدون گروه‌بندی</option>
                        <option value="year">سال</option>
                        <option value="quarter">فصل</option>
                        <option value="month">ماه</option>
                        <option value="week">هفته</option>
                        <option value="day">روز</option>
                      </select>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* KPI Number Formatting */}
          {chartType === 'kpi' && (
            <div className="border border-gray-200 rounded-xl p-4 space-y-4">
              <label className="block text-sm font-medium text-gray-700">قالب عدد</label>

              {/* Format type */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">نوع قالب</label>
                <select
                  value={kpiFormat.type}
                  onChange={(e) => setKpiFormat({ ...kpiFormat, type: e.target.value as KpiFormat['type'] })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                >
                  <option value="auto">خودکار</option>
                  <option value="number">عدد</option>
                  <option value="currency">ارز</option>
                  <option value="percentage">درصد</option>
                </select>
              </div>

              {/* Currency symbol (only for currency) */}
              {kpiFormat.type === 'currency' && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">نماد ارز</label>
                  <input
                    type="text"
                    value={kpiFormat.currency}
                    onChange={(e) => setKpiFormat({ ...kpiFormat, currency: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                    placeholder="$"
                    maxLength={5}
                  />
                </div>
              )}

              {/* Decimal places */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">اعداد اعشاری: {kpiFormat.decimals}</label>
                <input
                  type="range"
                  min={0}
                  max={10}
                  value={kpiFormat.decimals}
                  onChange={(e) => setKpiFormat({ ...kpiFormat, decimals: parseInt(e.target.value) })}
                  className="w-full accent-indigo-600"
                />
                <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
                  <span>0</span>
                  <span>5</span>
                  <span>10</span>
                </div>
              </div>

              {/* Prefix */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">پیشوند</label>
                <input
                  type="text"
                  value={kpiFormat.prefix}
                  onChange={(e) => setKpiFormat({ ...kpiFormat, prefix: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  placeholder="مثلاً: "
                  maxLength={10}
                />
              </div>

              {/* Suffix */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">پسوند</label>
                <input
                  type="text"
                  value={kpiFormat.suffix}
                  onChange={(e) => setKpiFormat({ ...kpiFormat, suffix: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  placeholder="مثلاً: تومان"
                  maxLength={10}
                />
              </div>

              {/* Preview */}
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <span className="text-[10px] text-gray-400 block mb-1">پیش‌نمایش</span>
                <span className="text-lg font-bold text-indigo-600">
                  {formatKpiValue(12345.6789, kpiFormat)}
                </span>
              </div>
            </div>
          )}

          {/* Save */}
          <button
            onClick={handleSave}
            className="w-full py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition"
          >
            ذخیره تنظیمات
          </button>
        </div>
      </div>
    </div>
  )
}
