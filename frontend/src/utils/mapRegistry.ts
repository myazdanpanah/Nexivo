/**
 * ECharts map registration utility.
 * Registers GeoJSON data so that ECharts `series.map` can reference map names.
 *
 * Usage:
 *   await registerMap('iran', '/maps/iran.json')
 *   // Then in chart option: series: [{ type: 'map', map: 'iran' }]
 */

import * as echarts from 'echarts'

const registeredMaps = new Set<string>()

/**
 * Register a GeoJSON map by fetching it from a URL and calling echarts.registerMap.
 * Idempotent — safe to call multiple times with the same name.
 */
export async function registerMap(
  name: string,
  geoJsonUrl: string,
): Promise<void> {
  if (registeredMaps.has(name)) return

  try {
    const response = await fetch(geoJsonUrl)
    if (!response.ok) throw new Error(`Failed to fetch map: ${response.statusText}`)
    const geoJson = await response.json()
    echarts.registerMap(name, geoJson)
    registeredMaps.add(name)
  } catch (err) {
    console.error(`[mapRegistry] Failed to register map "${name}":`, err)
    throw err
  }
}

/**
 * Check if a map is already registered.
 */
export function isMapRegistered(name: string): boolean {
  return registeredMaps.has(name)
}
