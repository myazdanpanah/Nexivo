/**
 * KPI number formatting utility.
 * Shared between ChartWidget rendering and the WidgetConfigPanel preview.
 */

export interface KpiFormat {
  type: 'auto' | 'number' | 'currency' | 'percentage'
  currency: string
  decimals: number
  prefix: string
  suffix: string
}

export const DEFAULT_KPI_FORMAT: KpiFormat = {
  type: 'auto',
  currency: '$',
  decimals: 0,
  prefix: '',
  suffix: '',
}

export function formatKpiValue(raw: number, fmt?: KpiFormat): string {
  if (!fmt || fmt.type === 'auto') {
    // Compact notation
    const compact =
      raw >= 1_000_000
        ? `${(raw / 1_000_000).toFixed(1)}M`
        : raw >= 1_000
          ? `${(raw / 1_000).toFixed(1)}K`
          : raw.toLocaleString()
    return compact
  }

  const dec = fmt.decimals ?? 0
  let formatted: string

  if (fmt.type === 'currency') {
    formatted = `${fmt.currency || '$'}${raw.toLocaleString(undefined, {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    })}`
  } else if (fmt.type === 'percentage') {
    formatted = `${(raw * 100).toLocaleString(undefined, {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    })}%`
  } else {
    // number
    formatted = raw.toLocaleString(undefined, {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    })
  }

  const prefix = fmt.prefix || ''
  const suffix = fmt.suffix ? ` ${fmt.suffix}` : ''
  return `${prefix}${formatted}${suffix}`
}
