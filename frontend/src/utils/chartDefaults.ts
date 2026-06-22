/**
 * Default ECharts configurations for different chart types.
 */

import type { EChartsOption } from 'echarts'

const baseTheme = {
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: "'Vazirmatn', Tahoma, Arial, sans-serif",
  },
}

export function getChartDefaults(chartType: string): EChartsOption {
  const base: EChartsOption = {
    ...baseTheme,
    grid: {
      top: 40,
      right: 20,
      bottom: 30,
      left: 50,
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
    },
  }

  switch (chartType) {
    case 'bar':
    case 'stacked_bar':
      return {
        ...base,
        xAxis: {
          type: 'category',
          data: [],
        },
        yAxis: {
          type: 'value',
        },
        series: [],
      }

    case 'line':
      return {
        ...base,
        xAxis: {
          type: 'category',
          data: [],
        },
        yAxis: {
          type: 'value',
        },
        series: [],
      }

    case 'pie':
    case 'donut':
      return {
        ...base,
        tooltip: {
          trigger: 'item',
        },
        series: [
          {
            type: 'pie',
            radius: chartType === 'donut' ? ['45%', '70%'] : ['0%', '70%'],
            data: [],
          },
        ],
      }

    case 'area':
      return {
        ...base,
        xAxis: {
          type: 'category',
          data: [],
          boundaryGap: false,
        },
        yAxis: {
          type: 'value',
        },
        series: [],
      }

    case 'scatter':
      return {
        ...base,
        xAxis: {
          type: 'value',
        },
        yAxis: {
          type: 'value',
        },
        series: [],
      }

    case 'gauge':
      return {
        ...base,
        series: [
          {
            type: 'gauge',
            detail: { formatter: '{value}' },
            data: [{ value: 0, name: '' }],
          },
        ],
      }

    default:
      return base
  }
}
