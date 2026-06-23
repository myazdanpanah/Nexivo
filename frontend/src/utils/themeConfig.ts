/**
 * Dashboard theme configuration.
 * Controls global styling for charts and widgets.
 */

export interface WidgetStyle {
  bgColor: string
  borderRadius: number
  shadow: 'none' | 'sm' | 'md' | 'lg'
  legendPosition: 'top' | 'bottom' | 'left' | 'right' | 'hidden'
  axisLabelFontSize: number
  tooltipStyle: 'light' | 'dark'
}

export interface ConditionalFormat {
  column: string
  type: 'threshold' | 'colorScale'
  thresholds?: Array<{ value: number; color: string; label?: string }>
  colorScale?: { min: number; max: number; lowColor: string; highColor: string }
}

export interface DashboardTheme {
  paletteId: string
  darkMode: boolean
  widgetStyle: WidgetStyle
  conditionalFormats: ConditionalFormat[]
}

export const DEFAULT_WIDGET_STYLE: WidgetStyle = {
  bgColor: 'transparent',
  borderRadius: 16,
  shadow: 'sm',
  legendPosition: 'bottom',
  axisLabelFontSize: 11,
  tooltipStyle: 'light',
}

export const DEFAULT_THEME: DashboardTheme = {
  paletteId: 'nexivo',
  darkMode: false,
  widgetStyle: { ...DEFAULT_WIDGET_STYLE },
  conditionalFormats: [],
}

/**
 * Get shadow CSS class from shadow level.
 */
export function getShadowClass(shadow: WidgetStyle['shadow']): string {
  switch (shadow) {
    case 'none': return ''
    case 'sm': return 'shadow-sm'
    case 'md': return 'shadow-md'
    case 'lg': return 'shadow-lg'
    default: return 'shadow-sm'
  }
}

/**
 * Get background class for dark mode.
 */
export function getDarkModeClasses(dark: boolean): { bg: string; card: string; text: string; border: string } {
  if (!dark) {
    return { bg: 'bg-gray-50', card: 'bg-white', text: 'text-gray-900', border: 'border-gray-200' }
  }
  return { bg: 'bg-gray-900', card: 'bg-gray-800', text: 'text-gray-100', border: 'border-gray-700' }
}
