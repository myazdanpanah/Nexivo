import { useState, useEffect, useRef } from 'react'
import { useDashboardStore, type DashboardPageConfig, type DashboardFilterControl } from '../store/dashboardStore'
import { useAuthStore } from '../store/authStore'
import { useToast } from './Toast'
import { Plus, GripVertical, Pencil, Check, Copy, Trash2, Download, Upload, Shield, MoreVertical, X } from 'lucide-react'
import api from '../api/client'

const ROLE_OPTIONS = [
  { value: 'ceo', label: 'مدیرعامل' },
  { value: 'finance', label: 'مالی' },
  { value: 'sales', label: 'فروش' },
  { value: 'admin', label: 'مدیر سیستم' },
]

export default function PageNavBar() {
  const { pages, activePageId, setActivePage, addPage, updatePage, removePage, setPages, dashboardId } = useDashboardStore()
  const { toast } = useToast()
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [showMenu, setShowMenu] = useState<string | null>(null)
  const [showAccessControl, setShowAccessControl] = useState<string | null>(null)
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  const menuContainerRef = useRef<HTMLDivElement>(null)

  // Close menus on outside click
  useEffect(() => {
    if (!showMenu && !showAccessControl) return
    const handler = (e: MouseEvent) => {
      if (menuContainerRef.current && !menuContainerRef.current.contains(e.target as Node)) {
        setShowMenu(null)
        setShowAccessControl(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showMenu, showAccessControl])

  const handleAddPage = async () => {
    if (!dashboardId) return
    const order = pages.length
    try {
      const res = await api.post(`/dashboards/${dashboardId}/pages/`, {
        name: `صفحه ${order + 1}`,
        order,
      })
      addPage({
        id: String(res.data.id),
        name: res.data.name,
        order: res.data.order,
        layout: res.data.layout || [],
        widgets: [],
      })
      toast('صفحه جدید اضافه شد', 'success')
    } catch {
      toast('خطا در افزودن صفحه', 'error')
    }
  }

  const handleRename = async (pageId: string) => {
    if (!dashboardId || !renameValue.trim()) return
    try {
      await api.put(`/dashboards/${dashboardId}/pages/${pageId}/`, {
        name: renameValue.trim(),
      })
      updatePage(pageId, { name: renameValue.trim() })
      setRenamingId(null)
      toast('نام صفحه تغییر کرد', 'success')
    } catch {
      toast('خطا در تغییر نام', 'error')
    }
  }

  const handleDeletePage = async (pageId: string) => {
    if (!dashboardId) return
    if (pages.length <= 1) {
      toast('امکان حذف آخرین صفحه وجود ندارد', 'error')
      return
    }
    if (!window.confirm('آیا از حذف این صفحه و تمام نمودارهای آن اطمینان دارید؟ این عمل غیرقابل بازگشت است.')) {
      return
    }
    try {
      await api.delete(`/dashboards/${dashboardId}/pages/${pageId}/`)
      removePage(pageId)
      setShowMenu(null)
      toast('صفحه حذف شد', 'success')
    } catch {
      toast('خطا در حذف صفحه', 'error')
    }
  }

  const handleDuplicatePage = async (pageId: string) => {
    if (!dashboardId) return
    try {
      const res = await api.post(`/dashboards/${dashboardId}/pages/${pageId}/duplicate/`)
      const newPage: DashboardPageConfig = {
        id: String(res.data.id),
        name: res.data.name,
        order: res.data.order,
        layout: res.data.layout || [],
        filterControls: (res.data.filter_controls as DashboardFilterControl[]) || [],
        widgets: ((res.data.widgets || []) as Array<Record<string, unknown>>).map((w) => ({
          id: String(w.id),
          title: w.title as string,
          chartType: w.chart_type as string,
          datasetId: w.dataset as number | null,
          chartConfig: (w.chart_config as Record<string, unknown>) || {},
          queryConfig: (w.query_config as Record<string, unknown>) || {},
          columnTypes: (w.column_types as Record<string, string>) || {},
        })),
      }
      addPage(newPage)
      setShowMenu(null)
      toast('صفحه کپی شد', 'success')
    } catch {
      toast('خطا در کپی صفحه', 'error')
    }
  }

  const handleExportPage = async (pageId: string) => {
    if (!dashboardId) return
    try {
      const res = await api.get(`/dashboards/${dashboardId}/pages/${pageId}/export/`)
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `page-${pageId}.json`
      a.click()
      URL.revokeObjectURL(url)
      setShowMenu(null)
      toast('خروجی JSON دانلود شد', 'success')
    } catch {
      toast('خطا در خروجی گرفتن', 'error')
    }
  }

  const handleImportPage = async () => {
    if (!dashboardId) return
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json'
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return
      try {
        const text = await file.text()
        const data = JSON.parse(text)
        const res = await api.post(`/dashboards/${dashboardId}/pages/import/`, data)
        const newPage: DashboardPageConfig = {
          id: String(res.data.id),
          name: res.data.name,
          order: res.data.order,
          layout: res.data.layout || [],
          filterControls: (res.data.filter_controls as DashboardFilterControl[]) || [],
          widgets: ((res.data.widgets || []) as Array<Record<string, unknown>>).map((w) => ({
            id: String(w.id),
            title: w.title as string,
            chartType: w.chart_type as string,
            datasetId: w.dataset as number | null,
            chartConfig: (w.chart_config as Record<string, unknown>) || {},
            queryConfig: (w.query_config as Record<string, unknown>) || {},
            columnTypes: (w.column_types as Record<string, string>) || {},
          })),
        }
        addPage(newPage)
        toast('صفحه وارد شد', 'success')
      } catch {
        toast('خطا در وارد کردن صفحه', 'error')
      }
    }
    input.click()
  }

  const handleAccessControlToggle = async (pageId: string, role: string, checked: boolean) => {
    if (!dashboardId) return
    const page = pages.find((p) => p.id === pageId)
    if (!page) return
    const currentRoles = page.allowedRoles || []
    const allRoles = ROLE_OPTIONS.map((r) => r.value)
    let newRoles: string[]
    if (checked) {
      newRoles = [...currentRoles, role]
      if (newRoles.length === allRoles.length) newRoles = []
    } else {
      newRoles = currentRoles.filter((r) => r !== role)
    }
    try {
      await api.put(`/dashboards/${dashboardId}/pages/${pageId}/`, {
        allowed_roles: newRoles,
      })
      updatePage(pageId, { allowedRoles: newRoles } as Partial<DashboardPageConfig>)
      toast('دسترسی صفحه به‌روز شد', 'success')
    } catch {
      toast('خطا در به‌روزرسانی دسترسی', 'error')
    }
  }

  const startRename = (page: DashboardPageConfig) => {
    setRenamingId(page.id)
    setRenameValue(page.name)
    setShowMenu(null)
  }

  // Drag-and-drop handlers
  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDragIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverIndex(index)
  }

  const handleDragLeave = () => {
    setDragOverIndex(null)
  }

  const handleDrop = async (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault()
    setDragOverIndex(null)

    if (dragIndex === null || dragIndex === dropIndex) {
      setDragIndex(null)
      return
    }

    const newPages = [...pages]
    const [moved] = newPages.splice(dragIndex, 1)
    newPages.splice(dropIndex, 0, moved)

    const reordered = newPages.map((p, i) => ({ ...p, order: i }))
    setPages(reordered)
    setDragIndex(null)

    if (dashboardId) {
      api.put(`/dashboards/${dashboardId}/pages/reorder/`, {
        page_ids: reordered.map((p) => parseInt(p.id)),
      }).catch(() => {})
      toast('ترتیب صفحات ذخیره شد', 'success')
    }
  }

  const handleDragEnd = () => {
    setDragIndex(null)
    setDragOverIndex(null)
  }

  // Filter pages by role access for display
  const userRole = useAuthStore((s) => s.user?.role)
  const visiblePages = pages.filter((page) => {
    const pr = page.allowedRoles
    if (!pr || pr.length === 0) return true
    if (!userRole) return false
    return pr.includes(userRole)
  })

  // If active page is not visible, auto-select the first visible page
  useEffect(() => {
    if (activePageId && visiblePages.length > 0 && !visiblePages.find((p) => p.id === activePageId)) {
      setActivePage(visiblePages[0].id)
    }
  }, [activePageId, visiblePages, setActivePage])

  if (visiblePages.length === 0) return null

  // Menu item button component
  const MenuItem = ({ icon: Icon, label, onClick, danger }: { icon: React.ElementType; label: string; onClick: () => void; danger?: boolean }) => (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-3 py-2 text-xs rounded-lg transition ${
        danger
          ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
      }`}
    >
      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
      <span>{label}</span>
    </button>
  )

  // Get the page being edited in the menu
  const menuPage = showMenu ? visiblePages.find((p) => p.id === showMenu) : null
  const accessPage = showAccessControl ? visiblePages.find((p) => p.id === showAccessControl) : null

  return (
    <div ref={menuContainerRef} className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700" dir="rtl">
      {/* Tab row */}
      <div className="flex items-center gap-1 px-6 overflow-x-auto py-1 scrollbar-thin">
        {visiblePages.map((page, index) => {
          const isActive = page.id === activePageId
          const pageRoles = page.allowedRoles
          return (
            <div
              key={page.id}
              className={`relative group flex items-center transition-all ${
                dragOverIndex === index && dragIndex !== index ? 'border-l-2 border-indigo-500' : ''
              }`}
              draggable={pages.length > 1}
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, index)}
              onDragEnd={handleDragEnd}
            >
              {renamingId === page.id ? (
                <div className="flex items-center gap-1 px-2 py-1">
                  <input
                    type="text"
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRename(page.id)
                      if (e.key === 'Escape') setRenamingId(null)
                    }}
                    onBlur={() => handleRename(page.id)}
                    autoFocus
                    className="px-2 py-1 text-sm border border-indigo-300 dark:border-indigo-600 dark:bg-gray-800 dark:text-gray-200 rounded-lg outline-none focus:ring-1 focus:ring-indigo-500 min-w-[100px]"
                  />
                  <button
                    onClick={() => handleRename(page.id)}
                    className="p-1 text-indigo-600 hover:text-indigo-800"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setActivePage(page.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition rounded-t-lg border-b-2 ${
                    isActive
                      ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border-indigo-600'
                      : 'text-gray-500 dark:text-gray-400 border-transparent hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800'
                  } ${dragIndex === index ? 'opacity-50' : ''}`}
                >
                  {pages.length > 1 && (
                    <GripVertical
                      className="w-3 h-3 text-gray-400 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition"
                    />
                  )}
                  {page.name}
                  {pageRoles && pageRoles.length > 0 && (
                    <Shield className="w-3 h-3 text-amber-500" />
                  )}
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowMenu(showMenu === page.id ? null : page.id)
                      setShowAccessControl(null)
                    }}
                    className="p-0.5 text-gray-400 hover:text-gray-600 rounded cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
                    title="منوی صفحه"
                  >
                    <MoreVertical className="w-3.5 h-3.5" />
                  </span>
                </button>
              )}
            </div>
          )
        })}

        {/* Add page button */}
        <button
          onClick={handleAddPage}
          className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
          title="افزودن صفحه جدید"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleImportPage}
          className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
          title="وارد کردن صفحه"
        >
          <Upload className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Inline menu panel — scrolls within the tab section */}
      {menuPage && showMenu && (
        <div className="border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-850 px-6 py-2">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">{menuPage.name}</span>
            <button
              onClick={() => setShowMenu(null)}
              className="p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            <MenuItem icon={Pencil} label="تغییر نام" onClick={() => startRename(menuPage)} />
            <MenuItem icon={Copy} label="کپی صفحه" onClick={() => handleDuplicatePage(menuPage.id)} />
            <MenuItem icon={Download} label="خروجی JSON" onClick={() => handleExportPage(menuPage.id)} />
            <MenuItem
              icon={Shield}
              label="کنترل دسترسی"
              onClick={() => {
                setShowMenu(null)
                setShowAccessControl(showAccessControl === menuPage.id ? null : menuPage.id)
              }}
            />
            {pages.length > 1 && (
              <MenuItem icon={Trash2} label="حذف صفحه" onClick={() => handleDeletePage(menuPage.id)} danger />
            )}
          </div>
        </div>
      )}

      {/* Inline access control panel */}
      {accessPage && showAccessControl && (
        <div className="border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-850 px-6 py-2">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-3 h-3 text-amber-500" />
            <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">نقش‌های مجاز — {accessPage.name}</span>
            <button
              onClick={() => setShowAccessControl(null)}
              className="p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
          <div className="flex flex-wrap gap-3">
            {ROLE_OPTIONS.map((role) => {
              const pageRoles = accessPage.allowedRoles
              const checked = !pageRoles || pageRoles.length === 0 || pageRoles.includes(role.value)
              return (
                <label
                  key={role.value}
                  className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-700 rounded px-2 py-1 cursor-pointer transition border border-gray-200 dark:border-gray-600"
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => handleAccessControlToggle(accessPage.id, role.value, e.target.checked)}
                    className="w-3 h-3 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                  />
                  {role.label}
                </label>
              )
            })}
          </div>
          <p className="text-[10px] text-gray-400 mt-1.5">بدون انتخاب = همه نقش‌ها مجازند</p>
        </div>
      )}
    </div>
  )
}
