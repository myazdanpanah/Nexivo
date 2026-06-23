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

    case 'heatmap':
      return {
        ...base,
        tooltip: {
          position: 'top',
        },
        grid: {
          top: 40,
          right: 80,
          bottom: 60,
          left: 80,
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: [],
          splitArea: { show: true },
        },
        yAxis: {
          type: 'category',
          data: [],
          splitArea: { show: true },
        },
        visualMap: {
          min: 0,
          max: 100,
          calculable: true,
          orient: 'vertical' as const,
          right: 0,
          top: 'center',
        },
        series: [],
      }

    case 'treemap':
      return {
        ...base,
        tooltip: {
          formatter: '{b}: {c}',
        },
        series: [],
      }

    case 'sankey':
      return {
        ...base,
        tooltip: {
          trigger: 'item' as const,
        },
        series: [],
      }

    case 'funnel':
      return {
        ...base,
        tooltip: {
          trigger: 'item' as const,
          formatter: '{b}: {c}',
        },
        series: [],
      }

    case 'radar':
      return {
        ...base,
        tooltip: {},
        radar: {
          indicator: [],
        },
        series: [],
      }

    case 'graph':
      return {
        ...base,
        tooltip: {},
        series: [],
      }

    case 'map':
      return {
        ...base,
        tooltip: {
          trigger: 'item' as const,
        },
        visualMap: {
          min: 0,
          max: 100,
          calculable: true,
          inRange: {
            color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695'],
          },
          text: ['بالا', 'پایین'],
          textStyle: {
            fontFamily: "'Vazirmatn', Tahoma, Arial, sans-serif",
          },
        },
        series: [],
      }

    default:
      return base
  }
}
