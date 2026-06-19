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
      return {
        ...base,
        tooltip: {
          trigger: 'item',
        },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
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

    default:
      return base
  }
}
