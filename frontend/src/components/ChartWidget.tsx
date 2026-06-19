import { useEffect, useState, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import { applyRTL } from '../utils/rtlConfig'
import { getChartDefaults } from '../utils/chartDefaults'
import api from '../api/client'

interface Widget {
  id: string
  title: string
  chartType: string
  datasetId: number | null
  chartConfig: Record<string, unknown>
  queryConfig: Record<string, unknown>
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

  // For pie chart
  if (chartType === 'pie') {
    const labelCol = columns[0]
    const valueCol = columns.length > 1 ? columns[1] : columns[0]
    const pieData = data.map((row) => ({
      name: String(row[labelCol] ?? ''),
      value: Number(row[valueCol]) || 0,
    }))

    const pieDefaults = getChartDefaults('pie') as Record<string, unknown>
    return {
      ...pieDefaults,
      ...customConfig,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [
        {
          type: 'pie',
          radius: ['35%', '65%'],
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

  // For bar, line, area charts — use first column as category, remaining as series
  const categoryCol = columns[0]
  const categoryData = data.map((row) => String(row[categoryCol] ?? ''))
  const valueCols = columns.slice(1)

  const seriesColors = [
    '#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6',
    '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#64748b',
  ]

  const series = valueCols.map((col, idx) => ({
    name: col,
    type: chartType === 'area' ? 'line' : chartType,
    data: data.map((row) => Number(row[col]) || 0),
    smooth: chartType === 'line' || chartType === 'area',
    areaStyle: chartType === 'area' ? { opacity: 0.3 } : undefined,
    itemStyle: {
      color: seriesColors[idx % seriesColors.length],
      borderRadius: chartType === 'bar' ? [4, 4, 0, 0] : undefined,
    },
    barMaxWidth: 40,
  }))

  return {
    ...defaults,
    ...customConfig,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: chartType === 'bar' ? 'shadow' : 'cross',
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
  const [option, setOption] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [tableData, setTableData] = useState<{ columns: string[]; rows: Record<string, unknown>[] } | null>(null)

  const fetchData = useCallback(async () => {
    // Clear table data when fetching new data
    setTableData(null)

    if (!widget.datasetId) {
      setOption({
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
      })
      return
    }

    setLoading(true)

    try {
      const res = await api.post(`/datasets/${widget.datasetId}/query/`, {
        columns: widget.queryConfig?.columns || undefined,
        filters: widget.queryConfig?.filters || [],
      })

      const result: QueryResult = res.data

      // Table chart: store data in separate state
      if (widget.chartType === 'table') {
        setTableData({ columns: result.columns, rows: result.data })
        setOption(null)
      } else {
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
        setOption(finalOption as Record<string, unknown>)
      }
    } catch (err: unknown) {
      console.error('Chart fetch error:', err)
      const message = err instanceof Error ? err.message : 'خطا در بارگذاری داده'
      setOption({
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: `خطا: ${message}`,
            fontSize: 12,
            fill: '#ef4444',
            textAlign: 'center',
          },
        },
      })
    } finally {
      setLoading(false)
    }
  }, [widget.datasetId, widget.chartType, widget.chartConfig, widget.queryConfig])

  useEffect(() => {
    fetchData()
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

  // Render table using separate state (not smuggled through ECharts option)
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

  if (!option) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        در حال بارگذاری...
      </div>
    )
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: '100%', width: '100%' }}
      opts={{ renderer: 'svg' }}
      notMerge={true}
    />
  )
}
