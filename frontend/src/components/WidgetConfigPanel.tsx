import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDashboardStore } from '../store/dashboardStore'
import api from '../api/client'
import { X, BarChart3, PieChart, TrendingUp, Table } from 'lucide-react'

interface WidgetConfigPanelProps {
  widgetId: string
  onClose: () => void
}

const chartTypes = [
  { value: 'bar', label: 'میله‌ای', icon: BarChart3 },
  { value: 'line', label: 'خطی', icon: TrendingUp },
  { value: 'pie', label: 'دایره‌ای', icon: PieChart },
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

  useEffect(() => {
    fetchDatasets()
  }, [])

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
        query_config: widget.queryConfig,
      })

      updateWidget(widgetId, {
        title,
        chartType,
        datasetId: selectedDatasetId,
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
