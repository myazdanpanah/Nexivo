/**
 * RTL configuration utilities for ECharts.
 * ECharts has no native RTL mode, so we manually adjust
 * chart options for Persian/Farsi layout.
 */

import type { EChartsOption } from 'echarts'

export function applyRTL(option: EChartsOption, isRTL: boolean): EChartsOption {
  if (!isRTL) return option

  const rtlOption = { ...option }

  // Reverse X axis for category/label charts only.
  // Value axes (scatter/line numeric) must NOT be flipped — it breaks the reading.
  if (rtlOption.xAxis && typeof rtlOption.xAxis === 'object' && !Array.isArray(rtlOption.xAxis)) {
    const xa = rtlOption.xAxis as { type?: string }
    if (xa.type !== 'value' && xa.type !== 'time' && xa.type !== 'log') {
      rtlOption.xAxis = {
        ...rtlOption.xAxis,
        inverse: true,
      }
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
