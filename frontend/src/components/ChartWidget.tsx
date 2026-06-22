import { useEffect, useState, useCallback, useRef } from 'react'
import * as echarts from 'echarts'
import { applyRTL } from '../utils/rtlConfig'
import { getChartDefaults } from '../utils/chartDefaults'
import { formatKpiValue, type KpiFormat } from '../utils/kpiFormat'
import api from '../api/client'

interface Widget {
  id: string
  title: string
  chartType: string
  datasetId: number | null
  chartConfig: Record<string, unknown>
  queryConfig: Record<string, unknown>
}

/**
 * For chart types that need aggregation, auto-build a metrics map.
 * Convention: first column = dimension (GROUP BY), rest = metrics (SUM).
 * If the widget already carries explicit metrics in queryConfig, use those.
 */
function buildMetrics(
  chartType: string,
  queryConfig: Record<string, unknown> | undefined
): Record<string, string> | undefined {
  // Tables never aggregate
  if (chartType === 'table') return undefined

  // Use explicit metrics if provided
  if (queryConfig?.metrics && typeof queryConfig.metrics === 'object') {
    const m = queryConfig.metrics as Record<string, string>
    return Object.keys(m).length > 0 ? m : undefined
  }

  const cols = (queryConfig?.columns as string[]) || []
  if (cols.length === 0) return undefined

  // KPI: no dimension — all columns are metrics
  if (chartType === 'kpi') {
    const metrics: Record<string, string> = {}
    for (const col of cols) {
      metrics[col] = 'SUM'
    }
    return metrics
  }

  // Bar/line/pie/area: first column = dimension, rest = SUM metrics
  if (cols.length <= 1) return undefined
  const metrics: Record<string, string> = {}
  for (let i = 1; i < cols.length; i++) {
    metrics[cols[i]] = 'SUM'
  }
  return metrics
}

interface ChartWidgetProps {
  widget: Widget
}

interface QueryResult {
  columns: string[]
  data: Record<string, unknown>[]
  row_count: number
}

function buildChartOption(
  chartType: string,
  queryResult: QueryResult,
  customConfig: Record<string, unknown>
): Record<string, unknown> {
  const { columns, data } = queryResult
  const defaults = getChartDefaults(chartType) as Record<string, unknown>

  if (data.length === 0 || columns.length === 0) {
    return {
      ...defaults,
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: 'داده\u200cای موجود نیست',
          fontSize: 14,
          fill: '#9ca3af',
        },
      },
    }
  }

  // For pie / donut chart
  if (chartType === 'pie' || chartType === 'donut') {
    const labelCol = columns[0]
    const valueCol = columns.length > 1 ? columns[1] : columns[0]
    const pieData = data.map((row) => ({
      name: String(row[labelCol] ?? ''),
      value: Number(row[valueCol]) || 0,
    }))

    const pieDefaults = getChartDefaults(chartType) as Record<string, unknown>
    return {
      ...pieDefaults,
      ...customConfig,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [
        {
          type: 'pie',
          radius: chartType === 'donut' ? ['45%', '70%'] : ['0%', '70%'],
          center: ['50%', '50%'],
          data: pieData,
          label: {
            show: true,
            formatter: '{b}\n{d}%',
            fontSize: 11,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.3)',
            },
          },
        },
      ],
    }
  }

  // For scatter plot
  if (chartType === 'scatter') {
    const xCol = columns[0]
    const yCol = columns.length > 1 ? columns[1] : columns[0]
    const sizeCol = columns.length > 2 ? columns[2] : null

    const scatterData = data.map((row) => {
      const x = Number(row[xCol]) || 0
      const y = Number(row[yCol]) || 0
      const size = sizeCol ? Number(row[sizeCol]) || 10 : 10
      return [x, y, size]
    })

    return {
      ...defaults,
      ...customConfig,
      tooltip: {
        trigger: 'item',
        formatter: `{a}<br/>${xCol}: {c0}<br/>${yCol}: {c1}`,
      },
      xAxis: { type: 'value', name: xCol },
      yAxis: { type: 'value', name: yCol },
      series: [{
        type: 'scatter',
        symbolSize: sizeCol ? (val: number[]) => Math.sqrt(val[2]) * 2 : 12,
        data: scatterData,
        itemStyle: { color: '#6366f1' },
      }],
    }
  }

  // For gauge chart
  if (chartType === 'gauge') {
    const valueCol = columns[columns.length - 1]
    const rawVal = data.length > 0 ? Number(data[0][valueCol]) || 0 : 0

    const gaugeDefaults = getChartDefaults('gauge') as Record<string, unknown>
    return {
      ...gaugeDefaults,
      ...customConfig,
      series: [{
        type: 'gauge',
        min: 0,
        max: 100,
        progress: { show: true, width: 18 },
        axisLine: { lineStyle: { width: 18 } },
        axisTick: { show: false },
        splitLine: { length: 10, lineStyle: { width: 2 } },
        pointer: { width: 5 },
        axisLabel: { distance: 20, fontSize: 10 },
        detail: { valueAnimation: true, fontSize: 20, offsetCenter: [0, '70%'], formatter: '{value}' },
        title: { offsetCenter: [0, '90%'] },
        data: [{ value: rawVal, name: valueCol }],
      }],
    }
  }

  // For bar, stacked_bar, line, area charts — first column = category, remaining = series
  const categoryCol = columns[0]
  const categoryData = data.map((row) => String(row[categoryCol] ?? ''))
  const valueCols = columns.slice(1)

  const seriesColors = [
    '#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6',
    '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#64748b',
  ]

  const isStacked = chartType === 'stacked_bar'
  const seriesType = isStacked ? 'bar' : (chartType === 'area' ? 'line' : chartType)

  const series = valueCols.map((col, idx) => ({
    name: col,
    type: seriesType,
    stack: isStacked ? 'total' : undefined,
    data: data.map((row) => Number(row[col]) || 0),
    smooth: chartType === 'line' || chartType === 'area',
    areaStyle: chartType === 'area' ? { opacity: 0.3 } : undefined,
    itemStyle: {
      color: seriesColors[idx % seriesColors.length],
      borderRadius: (chartType === 'bar' || isStacked) && !isStacked ? [4, 4, 0, 0] : undefined,
    },
    barMaxWidth: 40,
  }))

  return {
    ...defaults,
    ...customConfig,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: chartType === 'bar' || isStacked ? 'shadow' : 'cross',
      },
    },
    legend: valueCols.length > 1 ? { show: true, bottom: 0 } : { show: false },
    grid: {
      top: valueCols.length > 1 ? 40 : 30,
      right: 20,
      bottom: valueCols.length > 1 ? 40 : 30,
      left: 50,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: categoryData,
      axisLabel: {
        rotate: categoryData.length > 8 ? 45 : 0,
        fontSize: 11,
      },
    },
    yAxis: {
      type: 'value',
    },
    series,
  }
}

export default function ChartWidget({ widget }: ChartWidgetProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tableData, setTableData] = useState<{ columns: string[]; rows: Record<string, unknown>[] } | null>(null)
  const [kpiData, setKpiData] = useState<{ label: string; value: string; sub?: string } | null>(null)

  const usesECharts = widget.chartType !== 'table' && widget.chartType !== 'kpi'

  // Initialize and dispose chart instance (skip for non-ECharts types)
  useEffect(() => {
    if (!chartRef.current || !usesECharts) return

    const chart = echarts.init(chartRef.current, undefined, { renderer: 'svg' })
    chartInstance.current = chart

    // ResizeObserver handles both window resizes AND grid layout drag/resize
    const resizeObserver = new ResizeObserver(() => {
      if (!chart.isDisposed()) {
        chart.resize()
      }
    })
    resizeObserver.observe(chartRef.current)

    return () => {
      resizeObserver.disconnect()
      if (!chart.isDisposed()) {
        chart.dispose()
      }
      chartInstance.current = null
    }
  }, [usesECharts])

  const fetchData = useCallback(async () => {
    setTableData(null)
    setKpiData(null)
    setError(null)

    // For non-ECharts types (table, kpi), skip the chart-instance guard
    if (usesECharts && (!chartInstance.current || chartInstance.current.isDisposed())) {
      return
    }

    if (!widget.datasetId) {
      if (usesECharts && chartInstance.current && !chartInstance.current.isDisposed()) {
        chartInstance.current.setOption({
          graphic: {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
              text: 'منبع داده تعیین نشده\nاز پنل تنظیمات، مجموعه داده را انتخاب کنید',
              fontSize: 13,
              fill: '#9ca3af',
              textAlign: 'center',
              lineHeight: 20,
            },
          },
        }, true)
      }
      return
    }

    setLoading(true)

    try {
      const metrics = buildMetrics(widget.chartType, widget.queryConfig)
      const res = await api.post(`/datasets/${widget.datasetId}/query/`, {
        columns: widget.queryConfig?.columns || undefined,
        metrics: metrics || undefined,
        date_truncs: widget.queryConfig?.date_truncs || undefined,
        filters: widget.queryConfig?.filters || [],
      })

      const result: QueryResult = res.data

      // Re-check instance is still alive after async gap (ECharts types only)
      const chart = chartInstance.current
      if (usesECharts && (!chart || chart.isDisposed())) return

      if (widget.chartType === 'table') {
        setTableData({ columns: result.columns, rows: result.data })
      } else if (widget.chartType === 'kpi') {
        // KPI: show first metric value as big number with formatting
        const metricCols = Object.keys(metrics || {})
        const valueCol = metricCols[0] || result.columns[result.columns.length - 1]
        const rawVal = result.data.length > 0 ? result.data[0][valueCol] : 0
        const num = Number(rawVal) || 0

        const fmt = (widget.chartConfig as Record<string, unknown>)?.kpiFormat as KpiFormat | undefined
        const formatted = formatKpiValue(num, fmt)

        setKpiData({
          label: valueCol,
          value: formatted,
          sub: `${result.row_count} ردیف`,
        })
      } else {
        if (!chart) return
        const chartOption = buildChartOption(
          widget.chartType,
          result,
          widget.chartConfig || {}
        )
        const isRTL = document.documentElement.dir === 'rtl'
        const finalOption = applyRTL(
          chartOption as import('echarts').EChartsOption,
          isRTL
        )
        chart.setOption(finalOption as Record<string, unknown>, true)
      }
    } catch (err: unknown) {
      console.error('Chart fetch error:', err)
      const message = err instanceof Error ? err.message : 'خطا در بارگذاری داده'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [usesECharts, widget.datasetId, widget.chartType, widget.chartConfig, widget.queryConfig])

  useEffect(() => {
    // Small delay to ensure chart init effect runs first (StrictMode safe)
    const timer = setTimeout(() => fetchData(), 0)
    return () => clearTimeout(timer)
  }, [fetchData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          در حال بارگذاری...
        </div>
      </div>
    )
  }

  if (widget.chartType === 'table' && tableData) {
    return (
      <div className="h-full overflow-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-50">
              {tableData.columns.map((col) => (
                <th key={col} className="px-3 py-2 text-right font-medium text-gray-600 border-b">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.rows.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition">
                {tableData.columns.map((col) => (
                  <td key={col} className="px-3 py-1.5 text-right text-gray-800 border-b border-gray-100">
                    {row[col] != null ? String(row[col]) : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  // KPI card rendering
  if (widget.chartType === 'kpi') {
    if (error) {
      return (
        <div className="flex items-center justify-center h-full p-4">
          <span className="text-sm text-red-500 text-center">خطا: {error}</span>
        </div>
      )
    }
    if (kpiData) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-4">
          <span className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
            {kpiData.label}
          </span>
          <span className="text-3xl font-extrabold text-indigo-600 leading-none">
            {kpiData.value}
          </span>
          {kpiData.sub && (
            <span className="text-xs text-gray-400 mt-2">{kpiData.sub}</span>
          )}
        </div>
      )
    }
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        منبع داده تعیین نشده
      </div>
    )
  }

  // Table error display
  if (widget.chartType === 'table' && error) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <span className="text-sm text-red-500 text-center">خطا: {error}</span>
      </div>
    )
  }

  // ECharts error display (for bar/line/pie/area)
  if (error && !loading) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <span className="text-sm text-red-500 text-center">خطا: {error}</span>
      </div>
    )
  }

  return (
    <div
      ref={chartRef}
      style={{ height: '100%', width: '100%', minHeight: '200px' }}
    />
  )
}
