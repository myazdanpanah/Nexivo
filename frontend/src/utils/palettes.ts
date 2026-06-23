/**
 * Color palette system for Nexivo charts.
 * Provides preset palettes and supports custom user-defined palettes.
 */

export interface ColorPalette {
  id: string
  name: string
  nameEn: string
  colors: string[]
}

export const PRESET_PALETTES: ColorPalette[] = [
  {
    id: 'nexivo',
    name: 'نکسیوو',
    nameEn: 'Nexivo',
    colors: ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#64748b'],
  },
  {
    id: 'ocean',
    name: 'اقیانوس',
    nameEn: 'Ocean',
    colors: ['#0077b6', '#00b4d8', '#90e0ef', '#caf0f8', '#023e8a', '#0096c7', '#48cae4', '#ade8f4', '#03045e', '#005f73'],
  },
  {
    id: 'sunset',
    name: 'غروب',
    nameEn: 'Sunset',
    colors: ['#ff6b6b', '#feca57', '#ff9ff3', '#f368e0', '#ff9f43', '#ee5a24', '#f8c291', '#e55039', '#eb4d4b', '#b71540'],
  },
  {
    id: 'forest',
    name: 'جنگل',
    nameEn: 'Forest',
    colors: ['#2d6a4f', '#40916c', '#52b788', '#74c69d', '#95d5b2', '#1b4332', '#344e41', '#588157', '#a3b18a', '#dad7cd'],
  },
  {
    id: 'monochrome',
    name: 'تک‌رنگ',
    nameEn: 'Monochrome',
    colors: ['#1a1a2e', '#16213e', '#0f3460', '#533483', '#e94560', '#2c2c54', '#474787', '#aaabad', '#706fd3', '#3d3d6b'],
  },
  {
    id: 'pastel',
    name: 'پاستلی',
    nameEn: 'Pastel',
    colors: ['#a8dadc', '#457b9d', '#f1faee', '#e63946', '#1d3557', '#f4a261', '#2a9d8f', '#e9c46a', '#264653', '#283618'],
  },
  {
    id: 'neon',
    name: 'نئونی',
    nameEn: 'Neon',
    colors: ['#ff00ff', '#00ffff', '#ff0080', '#80ff00', '#ff8000', '#0080ff', '#ff0040', '#00ff80', '#8000ff', '#ffff00'],
  },
  {
    id: 'corporate',
    name: 'شرکتی',
    nameEn: 'Corporate',
    colors: ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed', '#0891b2', '#be123c', '#65a30d', '#c2410c', '#4f46e5'],
  },
]

export const DEFAULT_PALETTE = PRESET_PALETTES[0]

/**
 * Get a palette by ID. Returns the default palette if not found.
 */
export function getPalette(id: string): ColorPalette {
  return PRESET_PALETTES.find((p) => p.id === id) || DEFAULT_PALETTE
}

/**
 * Get colors from a palette, cycling if needed.
 */
export function getPaletteColors(paletteId: string, count: number): string[] {
  const palette = getPalette(paletteId)
  const colors: string[] = []
  for (let i = 0; i < count; i++) {
    colors.push(palette.colors[i % palette.colors.length])
  }
  return colors
}
