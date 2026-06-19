/**
 * RTL configuration utilities for ECharts.
 * ECharts has no native RTL mode, so we manually adjust
 * chart options for Persian/Farsi layout.
 */

import type { EChartsOption } from 'echarts'

export function applyRTL(option: EChartsOption, isRTL: boolean): EChartsOption {
  if (!isRTL) return option

  const rtlOption = { ...option }

  // Reverse X axis for horizontal charts
  if (rtlOption.xAxis && typeof rtlOption.xAxis === 'object' && !Array.isArray(rtlOption.xAxis)) {
    rtlOption.xAxis = {
      ...rtlOption.xAxis,
      inverse: true,
    }
  }

  // Adjust legend position
  if (rtlOption.legend && typeof rtlOption.legend === 'object') {
    rtlOption.legend = {
      ...rtlOption.legend,
      align: 'left' as const,
    }
  }

  // Adjust tooltip
  if (rtlOption.tooltip && typeof rtlOption.tooltip === 'object') {
    rtlOption.tooltip = {
      ...rtlOption.tooltip,
    }
  }

  return rtlOption
}

/**
 * Get RTL-aware default chart options.
 */
export function getRTLDefaults(isRTL: boolean): Partial<EChartsOption> {
  if (!isRTL) return {}

  return {
    legend: {
      align: 'left',
      right: 10,
    },
  }
}
