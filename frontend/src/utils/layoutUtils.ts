/**
 * Layout utility: auto-sizes grid items across breakpoints.
 *
 * When the browser window crosses a breakpoint boundary the grid items are
 * re-mapped so every widget fills its row on smaller screens while keeping
 * the desktop layout intact.
 */

import type { GridItem } from '../store/dashboardStore'

/**
 * Given a desktop layout, compute a responsive layout that maps into the
 * target number of columns.  Items wider than the target are clamped, and
 * items on the same row are stacked vertically when they would overlap.
 */
export function computeResponsiveLayout(
  desktopLayout: GridItem[],
  targetCols: number,
): GridItem[] {
  if (!desktopLayout.length) return []

  // Sort by y then x to preserve reading order
  const sorted = [...desktopLayout].sort((a, b) => a.y - b.y || a.x - b.x)

  const result: GridItem[] = []
  let cursorY = 0

  for (const item of sorted) {
    const w = Math.min(item.w, targetCols)
    // Place each item at x=0 (full width) in the target grid
    result.push({
      i: item.i,
      x: 0,
      y: cursorY,
      w,
      h: item.h,
    })
    cursorY += item.h
  }

  return result
}


