/**
 * Default ECharts configurations for different chart types.
 */

import type { EChartsOption } from 'echarts'

/** Font configuration stored on widget.chartConfig. */
export interface FontConfig {
  /** Axis/category/label text size (px). */
  labelSize?: number
  /** Value/number text size (px). */
  valueSize?: number
  /** Optional explicit font family override. */
  fontFamily?: string
}

/** Read a FontConfig off a chartConfig object (defensive). */
export function readFontConfig(cfg: Record<string, unknown> | undefined): FontConfig {
  const f = (cfg?.fontConfig as Record<string, unknown> | undefined) || {}
  return {
    labelSize: typeof f.labelSize === 'number' ? f.labelSize : undefined,
    valueSize: typeof f.valueSize === 'number' ? f.valueSize : undefined,
    fontFamily: typeof f.fontFamily === 'string' && f.fontFamily.trim()
      ? f.fontFamily
      : undefined,
  }
}

const BASE_FONT_FAMILY = "'Vazirmatn', Tahoma, Arial, sans-serif"

/** Resolve an effective font family for ECharts. */
export function resolveFontFamily(cfg: Record<string, unknown> | undefined): string {
  return readFontConfig(cfg).fontFamily || BASE_FONT_FAMILY
}

const baseTheme = {
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: BASE_FONT_FAMILY,
  },
}

export function getChartDefaults(chartType: string): EChartsOption {
  const base: EChartsOption = {
    ...baseTheme,
    // Titles render centered across all chart types.
    title: {
      left: 'center',
      textAlign: 'center',
      textVerticalAlign: 'top',
    },
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
