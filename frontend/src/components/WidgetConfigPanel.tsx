import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useDashboardStore } from '../store/dashboardStore'
import api from '../api/client'
import { X, BarChart3, PieChart, TrendingUp, Table } from 'lucide-react'

interface WidgetConfigPanelProps {
  widgetId: string
  onClose: () => void
}

const chartTypes = [
  { value: 'bar', label: 'میله\u200cای', icon: BarChart3 },
  { value: 'line', label: 'خطی', icon: TrendingUp },
  { value: 'pie', label: 'دایره\u200cای', icon: PieChart },
  { value: 'table', label: 'جدول', icon: Table },
]

interface Dataset {
  id: number
  name: string
  column_names: string[]
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

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId)

  useEffect(() => {
    fetchDatasets()
  }, [])

  // When dataset changes, auto-select all columns
  const prevDatasetIdRef = useRef<number | null>(selectedDatasetId)
  useEffect(() => {
    if (selectedDatasetId !== prevDatasetIdRef.current) {
      prevDatasetIdRef.current = selectedDatasetId
      if (selectedDataset) {
        setSelectedColumns(selectedDataset.column_names)
      } else {
        setSelectedColumns([])
      }
    }
  }, [selectedDatasetId, selectedDataset])

  const fetchDatasets = async () => {
    try {
      const res = await api.get('/datasets/')
      setDatasets(res.data)
    } catch {
      // ignore
    }
  }

  const handleSave = async () => {
    if (!widget) return

    try {
      await api.put(`/dashboards/${dashboardId}/widgets/${widgetId}/`, {
        title,
        chart_type: chartType,
        dataset: selectedDatasetId,
        chart_config: widget.chartConfig,
        query_config: {
          ...widget.queryConfig,
          columns: selectedColumns.length > 0 ? selectedColumns : undefined,
        },
      })

      updateWidget(widgetId, {
        title,
        chartType,
        datasetId: selectedDatasetId,
        queryConfig: {
          ...widget.queryConfig,
          columns: selectedColumns.length > 0 ? selectedColumns : undefined,
        },
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

          {/* Column Picker */}
          {selectedDataset && selectedDataset.column_names.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ستون\u200cها
                <span className="text-xs text-gray-400 mr-2">
                  ({chartType === 'table' ? 'ستون\u200cهای نمایشی' : 'ستون اول = دسته\u200cبندی، بقیه = مقادیر'})
                </span>
              </label>
              <div className="space-y-1.5 max-h-48 overflow-y-auto border border-gray-200 rounded-xl p-3">
                {selectedDataset.column_names.map((col) => (
                  <label
                    key={col}
                    className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-50 cursor-pointer transition"
                  >
                    <input
                      type="checkbox"
                      checked={selectedColumns.includes(col)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedColumns([...selectedColumns, col])
                        } else {
                          setSelectedColumns(selectedColumns.filter((c) => c !== col))
                        }
                      }}
                      className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">{col}</span>
                    {chartType !== 'table' && selectedColumns.indexOf(col) === 0 && selectedColumns.includes(col) && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-indigo-100 text-indigo-600 rounded-full">
                        دسته
                      </span>
                    )}
                    {chartType !== 'table' && selectedColumns.indexOf(col) > 0 && selectedColumns.includes(col) && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-600 rounded-full">
                        مقدار
                      </span>
                    )}
                  </label>
                ))}
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
                  onClick={() => setSelectedColumns([])}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  حذف انتخاب
                </button>
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
