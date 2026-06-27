/**
 * KPI number formatting utility.
 * Shared between ChartWidget rendering and the WidgetConfigPanel preview.
 * All numeric output is rendered with Persian digits (۰۱۲۳۴۵۶۷۸۹).
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

const PERSIAN_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']

/** Convert any Latin digits in a string to Persian digits. */
export function toPersianDigits(input: string | number): string {
  return String(input).replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)])
}

export function formatKpiValue(raw: number, fmt?: KpiFormat): string {
  if (!fmt || fmt.type === 'auto') {
    // Full number with locale formatting (no M/B/K abbreviations)
    return toPersianDigits(raw.toLocaleString('en-US'))
  }

  const dec = fmt.decimals ?? 0
  let formatted: string

  if (fmt.type === 'currency') {
    formatted = `${fmt.currency || '$'}${raw.toLocaleString('en-US', {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    })}`
  } else if (fmt.type === 'percentage') {
    formatted = `${(raw * 100).toLocaleString('en-US', {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    })}%`
  } else {
    // number
    formatted = raw.toLocaleString('en-US', {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec,
    })
  }

  const prefix = fmt.prefix || ''
  const suffix = fmt.suffix ? ` ${fmt.suffix}` : ''
  return toPersianDigits(`${prefix}${formatted}${suffix}`)
}
