import { useEffect, useState, useCallback, useRef } from 'react'
import * as echarts from 'echarts'
import { applyRTL } from '../utils/rtlConfig'
import { getChartDefaults } from '../utils/chartDefaults'
import { formatKpiValue, type KpiFormat } from '../utils/kpiFormat'
import { type DashboardFilter } from '../store/dashboardStore'
import { isMapRegistered, registerMap } from '../utils/mapRegistry'
import { getPaletteColors } from '../utils/palettes'
import api from '../api/client'

interface Widget {
  id: string
  title: string
  chartType: string
  datasetId: number | null
  chartConfig: Record<string, unknown>
  queryConfig: Record<string, unknown>
  columnTypes?: Record<string, string>
}

interface ChartWidgetProps {
  widget: Widget
  dashboardFilters?: DashboardFilter[]
  dashboardControlFilters?: Array<{ col: string; op: string; val: string | number | (string | number)[]; datasetId?: number | null }>
  onFilter?: (filter: DashboardFilter) => void
  onDrillDown?: (col: string, value: string) => void
  drillBreadcrumb?: Array<{ col: string; value: string }>
  onDrillUp?: (index: number) => void
}

/**
 * Chart types that do NOT use aggregation (raw rows only).
 */
const NO_AGG_TYPES = new Set(['table', 'sankey', 'graph'])

/**
 * Chart types where all selected columns are treated as metrics (no GROUP BY dimension).
 */
const ALL_METRIC_TYPES = new Set(['kpi'])

/** Column types that support numeric aggregation. */
const NUMERIC_TYPES = new Set([
  'BIGINT', 'INTEGER', 'SMALLINT', 'DOUBLE PRECISION',
  'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT', 'INT64', 'FLOAT64',
])

/** Check if a column type is numeric. */
function isNumericType(colType: string | undefined): boolean {
  return NUMERIC_TYPES.has((colType || '').toUpperCase())
}

function buildMetrics(
  chartType: string,
  queryConfig: Record<string, unknown> | undefined,
  columnTypes?: Record<string, string>
): Record<string, string> | undefined {
  // Charts that never aggregate
  if (NO_AGG_TYPES.has(chartType)) return undefined

  // Use explicit metrics if provided
  if (queryConfig?.metrics && typeof queryConfig.metrics === 'object') {
    const m = queryConfig.metrics as Record<string, string>
    if (Object.keys(m).length === 0) return undefined
    // Filter out metrics for columns not in the columns list (stale metrics)
    const cols = new Set((queryConfig?.columns as string[]) || [])
    const filtered: Record<string, string> = {}
    for (const [col, func] of Object.entries(m)) {
      if (cols.has(col)) {
        filtered[col] = func
      }
    }
    return Object.keys(filtered).length > 0 ? filtered : undefined
  }

  const cols = (queryConfig?.columns as string[]) || []
  if (cols.length === 0) return undefined

  // KPI: no dimension — all columns are metrics (only numeric)
  if (ALL_METRIC_TYPES.has(chartType)) {
    const metricCols = columnTypes
      ? cols.filter(c => isNumericType(columnTypes[c]))
      : cols.filter(c => !columnTypes || isNumericType(columnTypes[c]))
    if (metricCols.length === 0) return undefined
    const metrics: Record<string, string> = {}
    for (const col of metricCols) {
      metrics[col] = 'SUM'
    }
    return metrics
  }

  // Heatmap: first two columns = x/y dimensions, third = value metric
  if (chartType === 'heatmap') {
    if (cols.length >= 3 && (!columnTypes || isNumericType(columnTypes[cols[2]]))) {
      return { [cols[2]]: 'SUM' }
    }
    return undefined
  }

  // Treemap: first column = dimension, second = value metric
  if (chartType === 'treemap') {
    if (cols.length >= 2 && (!columnTypes || isNumericType(columnTypes[cols[1]]))) {
      return { [cols[1]]: 'SUM' }
    }
    return undefined
  }

  // Everything else: first column = dimension, rest = numeric SUM metrics
  const dimCount = 1
  const metricCols = cols.slice(dimCount)
  const numericMetricCols = columnTypes
    ? metricCols.filter(c => isNumericType(columnTypes[c]))
    : metricCols
  if (numericMetricCols.length === 0) return undefined
  const metrics: Record<string, string> = {}
  for (const col of numericMetricCols) {
    metrics[col] = 'SUM'
  }
  return metrics
}

interface QueryResult {
  columns: string[]
  data: Record<string, unknown>[]
  row_count: number
}

/** Default fallback colors when no palette is configured. */
const FALLBACK_COLORS = [
  '#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#64748b',
]

/** Resolve palette colors from chartConfig, falling back to defaults. Cycles colors as needed. */
function resolveColors(customConfig: Record<string, unknown>, count: number): string[] {
  let base: string[]
  const paletteId = customConfig.paletteId as string | undefined
  if (paletteId) {
    base = getPaletteColors(paletteId, Math.max(count, 10))
  } else {
    const colors = customConfig.colors as string[] | undefined
    base = (colors && colors.length > 0) ? colors : FALLBACK_COLORS
  }
  const result: string[] = []
  for (let i = 0; i < count; i++) {
    result.push(base[i % base.length])
  }
  return result
}

function buildChartOption(
  chartType: string,
  queryResult: QueryResult,
  customConfig: Record<string, unknown>
): Record<string, unknown> {
  const { columns, data } = queryResult
  const defaults = getChartDefaults(chartType) as Record<string, unknown>

  // Extract widget style overrides
  const ws = customConfig.widgetStyle as { legendPosition?: string; tooltipStyle?: string } | undefined
  const legendPos = ws?.legendPosition || 'bottom'
  const tooltipBg = ws?.tooltipStyle === 'dark' ? '#1a1a2e' : undefined
  const tooltipFg = ws?.tooltipStyle === 'dark' ? '#e2e8f0' : undefined

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

  // For heatmap chart — x/y dimensions + value
  if (chartType === 'heatmap') {
    const xCol = columns[0]
    const yCol = columns.length > 1 ? columns[1] : columns[0]
    const valueCol = columns.length > 2 ? columns[2] : columns[0]

    const xCats = [...new Set(data.map((r) => String(r[xCol] ?? '')))]
    const yCats = [...new Set(data.map((r) => String(r[yCol] ?? '')))]

    const heatData: [number, number, number][] = []
    let maxVal = 0
    for (const row of data) {
      const xi = xCats.indexOf(String(row[xCol] ?? ''))
      const yi = yCats.indexOf(String(row[yCol] ?? ''))
      const val = Number(row[valueCol]) || 0
      if (val > maxVal) maxVal = val
      heatData.push([xi, yi, val])
    }

    const heatmapDefaults = getChartDefaults('heatmap') as Record<string, unknown>
    return {
      ...heatmapDefaults,
      ...customConfig,
      tooltip: {
        position: 'top',
        formatter: (p: { value?: [number, number, number] }) => {
          const v = p.value || [0, 0, 0]
          return `${xCats[v[0]]} × ${yCats[v[1]]}<br/>مقدار: ${v[2]}`
        },
      },
      xAxis: { type: 'category' as const, data: xCats, splitArea: { show: true }, axisLabel: { fontSize: 11 } },
      yAxis: { type: 'category' as const, data: yCats, splitArea: { show: true }, axisLabel: { fontSize: 11 } },
      visualMap: {
        min: 0,
        max: maxVal || 100,
        calculable: true,
        orient: 'vertical' as const,
        right: 0,
        top: 'center',
        inRange: {
          color: ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
        },
      },
      grid: { top: 20, right: 80, bottom: 40, left: 80, containLabel: true },
      series: [{
        type: 'heatmap',
        data: heatData,
        label: { show: data.length <= 50, fontSize: 10 },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' },
        },
      }],
    }
  }

  // For treemap chart — hierarchical rectangles
  if (chartType === 'treemap') {
    const labelCol = columns[0]
    const valueCol = columns.length > 1 ? columns[1] : columns[0]

    const treemapData = data.map((row) => ({
      name: String(row[labelCol] ?? ''),
      value: Number(row[valueCol]) || 0,
    }))

    const treemapDefaults = getChartDefaults('treemap') as Record<string, unknown>
    return {
      ...treemapDefaults,
      ...customConfig,
      tooltip: {
        formatter: (p: { name?: string; value?: number }) => `${p.name}: ${p.value}`,
      },
      series: [{
        type: 'treemap',
        data: treemapData,
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: {
          show: true,
          formatter: '{b}',
          fontSize: 12,
          color: '#fff',
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 2,
          gapWidth: 2,
        },
        levels: [{
          itemStyle: { borderColor: '#fff', borderWidth: 4, gapWidth: 4 },
          upperLabel: { show: false },
        }],
      }],
    }
  }

  // For sankey chart — flow diagram
  if (chartType === 'sankey') {
    // Expect columns: source, target, value
    const srcCol = columns[0]
    const tgtCol = columns.length > 1 ? columns[1] : columns[0]
    const valCol = columns.length > 2 ? columns[2] : columns[0]

    const nodeSet = new Set<string>()
    const links: Array<{ source: string; target: string; value: number }> = []
    for (const row of data) {
      const src = String(row[srcCol] ?? '')
      const tgt = String(row[tgtCol] ?? '')
      const val = Number(row[valCol]) || 0
      nodeSet.add(src)
      nodeSet.add(tgt)
      links.push({ source: src, target: tgt, value: val })
    }
    const nodes = [...nodeSet].map((name) => ({ name }))

    const paletteColors = resolveColors(customConfig, nodes.length)
    const nodeColorMap: Record<string, string> = {}
    nodes.forEach((n, i) => { nodeColorMap[n.name] = paletteColors[i % paletteColors.length] })

    const sankeyDefaults = getChartDefaults('sankey') as Record<string, unknown>
    return {
      ...sankeyDefaults,
      ...customConfig,
      tooltip: { trigger: 'item' as const },
      series: [{
        type: 'sankey',
        data: nodes.map((n) => ({ ...n, itemStyle: { color: nodeColorMap[n.name] } })),
        links,
        orient: 'horizontal' as const,
        lineStyle: { color: 'gradient' as const, curveness: 0.5 },
        label: { fontSize: 11 },
        emphasis: { focus: 'adjacency' as const },
      }],
    }
  }

  // For funnel chart — conversion pipeline
  if (chartType === 'funnel') {
    const labelCol = columns[0]
    const valueCol = columns.length > 1 ? columns[1] : columns[0]

    const funnelData = data
      .map((row) => ({
        name: String(row[labelCol] ?? ''),
        value: Number(row[valueCol]) || 0,
      }))
      .sort((a, b) => b.value - a.value)

    const funnelDefaults = getChartDefaults('funnel') as Record<string, unknown>
    return {
      ...funnelDefaults,
      ...customConfig,
      tooltip: {
        trigger: 'item' as const,
        formatter: '{b}: {c}',
      },
      series: [{
        type: 'funnel',
        left: '10%',
        top: 20,
        bottom: 20,
        width: '80%',
        min: 0,
        max: funnelData.length > 0 ? funnelData[0].value : 100,
        minSize: '0%',
        maxSize: '100%',
        sort: 'descending' as const,
        gap: 2,
        label: {
          show: true,
          position: 'inside' as const,
          formatter: '{b}: {c}',
          fontSize: 12,
          color: '#fff',
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1,
        },
        emphasis: {
          label: { fontSize: 14 },
        },
        data: funnelData,
      }],
    }
  }

  // For radar chart — multi-axis comparison
  if (chartType === 'radar') {
    const dimCol = columns[0]
    const metricCols = columns.slice(1)
    if (metricCols.length === 0) return defaults

    // Build indicator from metric column names
    const indicator = metricCols.map((col) => {
      const maxVal = Math.max(...data.map((r) => Number(r[col]) || 0), 1)
      return { name: col, max: maxVal * 1.2 }
    })

    // Each row is a series
    const seriesData = data.map((row) => ({
      name: String(row[dimCol] ?? ''),
      value: metricCols.map((col) => Number(row[col]) || 0),
    }))

    const radarDefaults = getChartDefaults('radar') as Record<string, unknown>
    const radarColors = resolveColors(customConfig, seriesData.length)

    return {
      ...radarDefaults,
      ...customConfig,
      tooltip: {},
      legend: data.length > 1 ? { show: true, bottom: 0 } : { show: false },
      radar: {
        indicator,
        shape: 'polygon' as const,
        splitNumber: 5,
        axisName: { fontSize: 11 },
      },
      series: [{
        type: 'radar',
        data: seriesData.map((s, i) => ({
          ...s,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2 },
          areaStyle: { opacity: 0.15 },
          itemStyle: { color: radarColors[i % radarColors.length] },
        })),
      }],
    }
  }

  // For graph/network chart — relationship visualization
  if (chartType === 'graph') {
    // Expect columns: source, target, [weight]
    const srcCol = columns[0]
    const tgtCol = columns.length > 1 ? columns[1] : columns[0]
    const weightCol = columns.length > 2 ? columns[2] : null

    const nodeMap = new Map<string, number>()
    const links: Array<{ source: string; target: string; value?: number }> = []

    for (const row of data) {
      const src = String(row[srcCol] ?? '')
      const tgt = String(row[tgtCol] ?? '')
      nodeMap.set(src, (nodeMap.get(src) || 0) + 1)
      nodeMap.set(tgt, (nodeMap.get(tgt) || 0) + 1)
      links.push({
        source: src,
        target: tgt,
        value: weightCol ? Number(row[weightCol]) || 1 : 1,
      })
    }

    const nodes = [...nodeMap.entries()].map(([name, degree], i) => ({
      name,
      symbolSize: Math.min(30 + degree * 5, 60),
      itemStyle: { color: graphColors[i % graphColors.length] },
    }))

    const graphDefaults = getChartDefaults('graph') as Record<string, unknown>
    const graphColors = resolveColors(customConfig, nodes.length)
    return {
      ...graphDefaults,
      ...customConfig,
      tooltip: {},
      series: [{
        type: 'graph',
        layout: 'force' as const,
        data: nodes,
        links,
        roam: true,
        draggable: true,
        force: {
          repulsion: 200,
          edgeLength: [80, 160],
          gravity: 0.1,
        },
        label: {
          show: true,
          fontSize: 10,
          position: 'right' as const,
        },
        lineStyle: {
          color: '#ccc',
          curveness: 0.1,
        },
        emphasis: {
          focus: 'adjacency' as const,
          lineStyle: { width: 3 },
        },
      }],
    }
  }

  // For map chart — geographic visualization
  if (chartType === 'map') {
    const regionCol = columns[0]
    const valueCol = columns.length > 1 ? columns[1] : columns[0]
    const mapName = (customConfig as Record<string, unknown>).mapName as string || 'iran'

    const mapData = data.map((row) => ({
      name: String(row[regionCol] ?? ''),
      value: Number(row[valueCol]) || 0,
    }))

    // If the map isn't registered yet, throw so the caller can handle async loading
    if (!isMapRegistered(mapName)) {
      throw new Error(`MAP_NOT_REGISTERED:${mapName}`)
    }

    const mapDefaults = getChartDefaults('map') as Record<string, unknown>
    return {
      ...mapDefaults,
      ...customConfig,
      tooltip: {
        trigger: 'item' as const,
        formatter: (p: { name?: string; value?: number }) => `${p.name}: ${p.value}`,
      },
      visualMap: {
        min: 0,
        max: Math.max(...mapData.map((d) => d.value), 1),
        calculable: true,
        inRange: {
          color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695'],
        },
        text: ['بالا', 'پایین'],
        textStyle: {
          fontFamily: "'Vazirmatn', Tahoma, Arial, sans-serif",
        },
      },
      series: [{
        type: 'map',
        map: mapName,
        roam: true,
        label: { show: false },
        data: mapData,
        emphasis: {
          label: { show: true, fontSize: 12, fontWeight: 'bold' as const },
          itemStyle: { areaColor: '#f59e0b' },
        },
      }],
    }
  }

  // For bar, stacked_bar, line, area charts — first column = category, remaining = series
  const categoryCol = columns[0]
  const categoryData = data.map((row) => String(row[categoryCol] ?? ''))
  const valueCols = columns.slice(1)

  const barColors = resolveColors(customConfig, valueCols.length)
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
      color: barColors[idx % barColors.length],
      borderRadius: (chartType === 'bar' || isStacked) && !isStacked ? [4, 4, 0, 0] : undefined,
    },
    barMaxWidth: 40,
  }))

  return {
    ...defaults,
    ...customConfig,
    tooltip: {
      trigger: 'axis',
      backgroundColor: tooltipBg,
      textStyle: tooltipFg ? { color: tooltipFg } : undefined,
      axisPointer: {
        type: chartType === 'bar' || isStacked ? 'shadow' : 'cross',
      },
    },
    legend: valueCols.length > 1 ? (legendPos === 'hidden' ? { show: false } : { show: true, [legendPos]: 10 }) : { show: false },
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

export default function ChartWidget({
  widget,
  dashboardFilters = [],
  dashboardControlFilters = [],
  onFilter,
  onDrillDown,
  drillBreadcrumb = [],
  onDrillUp,
}: ChartWidgetProps) {
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
      const metrics = buildMetrics(widget.chartType, widget.queryConfig, widget.columnTypes)

      // Merge all filter sources: widget-level, dashboard control, cross-chart, and drill-down
      const widgetFilters = (widget.queryConfig?.filters as Array<{col: string; op: string; val: string | number | (string | number)[]}>) || []
      const widgetColumns = (widget.queryConfig?.columns as string[]) || []
      const drillFilters = (drillBreadcrumb || []).map((crumb) => ({
        col: crumb.col, op: 'eq' as const, val: crumb.value,
      }))
      const mergedFilters = [
        ...widgetFilters,
        // Dashboard-level control filters (only if the column exists in this widget's dataset and matches datasetId)
        ...dashboardControlFilters.filter((f) =>
          (f.datasetId === undefined || f.datasetId === null || f.datasetId === widget.datasetId) &&
          (widgetColumns.length === 0 || widgetColumns.includes(f.col))
        ),
        // Cross-chart filters from chart click interactions
        ...dashboardFilters
          .filter((f) => f.sourceWidgetId !== widget.id && widgetColumns.includes(f.col))
          .map((f) => ({ col: f.col, op: f.op, val: f.val })),
        ...drillFilters,
      ]

      const res = await api.post(`/datasets/${widget.datasetId}/query/`, {
        columns: widget.queryConfig?.columns || undefined,
        metrics: metrics || undefined,
        date_truncs: widget.queryConfig?.date_truncs || undefined,
        filters: mergedFilters.length > 0 ? mergedFilters : undefined,
      })

      const result: QueryResult = res.data

      const chart = chartInstance.current
      if (usesECharts && (!chart || chart.isDisposed())) return

      if (widget.chartType === 'table') {
        setTableData({ columns: result.columns, rows: result.data })
      } else if (widget.chartType === 'kpi') {
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

        // Add cross-chart filter click handler
        if (onFilter) {
          chart.off('click')
          chart.on('click', (params: { seriesType?: string; name?: string; value?: unknown }) => {
            // For pie/donut: click slice → filter by category
            if (params.seriesType === 'pie' && params.name) {
              const dimCol = result.columns[0]
              onFilter({
                col: dimCol,
                op: 'eq',
                val: params.name,
                sourceWidgetId: widget.id,
              })
            }
            // For bar/line/area: click bar → filter by category
            if ((params.seriesType === 'bar' || params.seriesType === 'line') && params.name) {
              const dimCol = result.columns[0]
              onFilter({
                col: dimCol,
                op: 'eq',
                val: params.name,
                sourceWidgetId: widget.id,
              })
            }
          })
        }
      }
    } catch (err: unknown) {
      console.error('Chart fetch error:', err)
      let message = 'خطا در بارگذاری داده'
      if (err instanceof Error && err.message.startsWith('MAP_NOT_REGISTERED:')) {
        const mapName = err.message.split(':')[1]
        const mapUrl = (widget.chartConfig as Record<string, unknown>)?.mapUrl as string | undefined
        if (mapUrl) {
          try {
            await registerMap(mapName, mapUrl)
            // Re-fetch and render after registering the map
            setLoading(true)
            const retryRes = await api.post(`/datasets/${widget.datasetId}/query/`, {
              columns: widget.queryConfig?.columns || undefined,
              metrics: buildMetrics(widget.chartType, widget.queryConfig, widget.columnTypes) || undefined,
              date_truncs: widget.queryConfig?.date_truncs || undefined,
            })
            const retryResult: QueryResult = retryRes.data
            const chart = chartInstance.current
            if (chart && !chart.isDisposed()) {
              const retryOption = buildChartOption(widget.chartType, retryResult, widget.chartConfig || {})
              const retryFinal = applyRTL(retryOption as import('echarts').EChartsOption, document.documentElement.dir === 'rtl')
              chart.setOption(retryFinal as Record<string, unknown>, true)
              setError(null)
            }
            return
          } catch {
            message = `خطا در بارگذاری فایل نقشه از آدرس: ${mapUrl}`
          }
        } else {
          message = `نقشه "${mapName}" ثبت نشده است. لطفاً فایل GeoJSON نقشه را در تنظیمات نمودار تنظیم کنید.`
        }
      } else if (err instanceof Error) {
        message = err.message
      }
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [usesECharts, widget, dashboardFilters, dashboardControlFilters, drillBreadcrumb, onFilter])

  useEffect(() => {
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
        {/* Drill-down breadcrumb */}
        {drillBreadcrumb.length > 0 && onDrillUp && (
          <div className="flex items-center gap-1 px-3 py-1.5 bg-indigo-50 text-xs border-b">
            <button onClick={() => onDrillUp(-1)} className="text-indigo-600 hover:text-indigo-800 font-medium">
              همه
            </button>
            {drillBreadcrumb.map((crumb, idx) => (
              <span key={idx} className="flex items-center gap-1">
                <span className="text-gray-400">/</span>
                <button
                  onClick={() => onDrillUp(idx)}
                  className="text-indigo-600 hover:text-indigo-800"
                >
                  {crumb.value}
                </button>
              </span>
            ))}
          </div>
        )}
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
                  <td
                    key={col}
                    className={`px-3 py-1.5 text-right text-gray-800 border-b border-gray-100 ${
                      onDrillDown ? 'cursor-pointer hover:bg-indigo-50' : ''
                    }`}
                    onClick={onDrillDown ? () => onDrillDown(col, String(row[col] ?? '')) : undefined}
                  >
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

  if (widget.chartType === 'table' && error) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <span className="text-sm text-red-500 text-center">خطا: {error}</span>
      </div>
    )
  }

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
