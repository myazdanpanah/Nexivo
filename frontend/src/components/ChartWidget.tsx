import { useEffect, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { applyRTL } from '../utils/rtlConfig'
import { getChartDefaults } from '../utils/chartDefaults'

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

export default function ChartWidget({ widget }: ChartWidgetProps) {
  const [option, setOption] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    if (!widget.datasetId) {
      // Show placeholder if no dataset
      setOption({
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: 'منبع داده تعیین نشده',
            fontSize: 14,
            fill: '#9ca3af',
          },
        },
      })
      return
    }

    // Build chart config from defaults + custom config
    const defaults = getChartDefaults(widget.chartType) as Record<string, unknown>
    const custom = widget.chartConfig || {}

    // Apply RTL
    const isRTL = document.documentElement.dir === 'rtl'
    const finalOption = applyRTL(
      { ...defaults, ...custom } as import('echarts').EChartsOption,
      isRTL
    )

    setOption(finalOption as Record<string, unknown>)
  }, [widget])

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
    />
  )
}
