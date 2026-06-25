/** Shared role constants used across the application. */
export const ALL_ROLES = [
  { value: 'ceo', label: 'مدیرعامل', color: 'bg-purple-100 text-purple-700' },
  { value: 'finance', label: 'مالی', color: 'bg-blue-100 text-blue-700' },
  { value: 'sales', label: 'فروش', color: 'bg-emerald-100 text-emerald-700' },
  { value: 'admin', label: 'مدیر سیستم', color: 'bg-amber-100 text-amber-700' },
] as const

export type RoleValue = typeof ALL_ROLES[number]['value']

export const ROLE_MAP = Object.fromEntries(
  ALL_ROLES.map((r) => [r.value, r])
) as Record<string, typeof ALL_ROLES[number]>
