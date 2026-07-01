/**
 * Widget size constraints per chart type.
 *
 * Defines minimum and maximum width (w) and height (h) in grid units
 * to prevent charts from being too small to render properly or
 * unreasonably large.
 */

export interface WidgetSizeConstraints {
  minW: number
  minH: number
  maxW: number
  maxH: number
}

const CONSTRAINTS: Record<string, WidgetSizeConstraints> = {
  kpi:           { minW: 2, minH: 2, maxW: 4, maxH: 4 },
  bar:           { minW: 3, minH: 3, maxW: 12, maxH: 8 },
  bar_horizontal:{ minW: 4, minH: 3, maxW: 12, maxH: 8 },
  stacked_bar:   { minW: 3, minH: 3, maxW: 12, maxH: 8 },
  line:          { minW: 3, minH: 3, maxW: 12, maxH: 8 },
  area:          { minW: 3, minH: 3, maxW: 12, maxH: 8 },
  pie:           { minW: 3, minH: 3, maxW: 8, maxH: 8 },
  donut:         { minW: 3, minH: 3, maxW: 8, maxH: 8 },
  scatter:       { minW: 4, minH: 4, maxW: 12, maxH: 10 },
  gauge:         { minW: 2, minH: 3, maxW: 6, maxH: 6 },
  heatmap:       { minW: 4, minH: 4, maxW: 12, maxH: 10 },
  treemap:       { minW: 4, minH: 3, maxW: 12, maxH: 8 },
  sankey:        { minW: 4, minH: 4, maxW: 12, maxH: 10 },
  funnel:        { minW: 3, minH: 4, maxW: 8, maxH: 10 },
  radar:         { minW: 3, minH: 3, maxW: 8, maxH: 8 },
  graph:         { minW: 4, minH: 4, maxW: 12, maxH: 10 },
  map:           { minW: 4, minH: 4, maxW: 12, maxH: 10 },
  leader_kpi:    { minW: 2, minH: 2, maxW: 6, maxH: 4 },
  table:         { minW: 3, minH: 3, maxW: 12, maxH: 12 },
}

const DEFAULT_CONSTRAINTS: WidgetSizeConstraints = { minW: 2, minH: 2, maxW: 12, maxH: 12 }

/** Get size constraints for a chart type. */
export function getWidgetConstraints(chartType: string): WidgetSizeConstraints {
  return CONSTRAINTS[chartType] || DEFAULT_CONSTRAINTS
}

/** Clamp a grid item to its chart type's size constraints. */
export function clampGridItem(
  item: { i: string; x: number; y: number; w: number; h: number },
  chartType: string,
): { i: string; x: number; y: number; w: number; h: number } {
  const c = getWidgetConstraints(chartType)
  return {
    i: item.i,
    x: item.x,
    y: item.y,
    w: Math.max(c.minW, Math.min(c.maxW, item.w)),
    h: Math.max(c.minH, Math.min(c.maxH, item.h)),
  }
}
