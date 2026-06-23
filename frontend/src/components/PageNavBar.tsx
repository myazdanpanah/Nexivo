import { useState, useEffect, useRef } from 'react'
import { useDashboardStore, type DashboardPageConfig, type DashboardFilterControl } from '../store/dashboardStore'
import { Plus, GripVertical, Pencil, Check, Copy, Trash2, Download, Upload } from 'lucide-react'
import api from '../api/client'

export default function PageNavBar() {
  const { pages, activePageId, setActivePage, addPage, updatePage, removePage, setPages, dashboardId } = useDashboardStore()
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [showMenu, setShowMenu] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  // Close context menu on outside click
  useEffect(() => {
    if (!showMenu) return
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showMenu])

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
    } catch {
      // ignore
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
    } catch {
      // ignore
    }
  }

  const handleDeletePage = async (pageId: string) => {
    if (!dashboardId) return
    if (pages.length <= 1) return
    try {
      await api.delete(`/dashboards/${dashboardId}/pages/${pageId}/`)
      removePage(pageId)
      setShowMenu(null)
    } catch {
      // ignore
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
    } catch {
      // ignore
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
    } catch {
      // ignore
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
      } catch {
        // ignore
      }
    }
    input.click()
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

    // Reorder pages
    const newPages = [...pages]
    const [moved] = newPages.splice(dragIndex, 1)
    newPages.splice(dropIndex, 0, moved)

    // Update orders
    const reordered = newPages.map((p, i) => ({ ...p, order: i }))
    setPages(reordered)
    setDragIndex(null)

    // Persist to backend
    if (dashboardId) {
      api.put(`/dashboards/${dashboardId}/pages/reorder/`, {
        page_ids: reordered.map((p) => parseInt(p.id)),
      }).catch(() => {})
    }
  }

  const handleDragEnd = () => {
    setDragIndex(null)
    setDragOverIndex(null)
  }

  if (pages.length === 0) return null

  return (
    <div className="bg-white border-b border-gray-200 px-6" dir="rtl">
      <div className="flex items-center gap-1 overflow-x-auto py-1 scrollbar-thin">
        {pages.map((page, index) => {
          const isActive = page.id === activePageId
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
                    className="px-2 py-1 text-sm border border-indigo-300 rounded-lg outline-none focus:ring-1 focus:ring-indigo-500 min-w-[100px]"
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
                      ? 'bg-indigo-50 text-indigo-700 border-indigo-600'
                      : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-gray-50'
                  } ${dragIndex === index ? 'opacity-50' : ''}`}
                >
                  {pages.length > 1 && (
                    <GripVertical
                      className="w-3 h-3 text-gray-400 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition"
                    />
                  )}
                  {page.name}
                  {isActive && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setShowMenu(showMenu === page.id ? null : page.id)
                      }}
                      className="p-0.5 text-gray-400 hover:text-gray-600 rounded"
                    >
                      <GripVertical className="w-3 h-3" />
                    </button>
                  )}
                </button>
              )}

              {/* Context menu */}
              {showMenu === page.id && (
                <div ref={menuRef} className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50 min-w-[160px]">
                  <button
                    onClick={() => startRename(page)}
                    className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                  >
                    <Pencil className="w-3 h-3" />
                    تغییر نام
                  </button>
                  <button
                    onClick={() => handleDuplicatePage(page.id)}
                    className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                  >
                    <Copy className="w-3 h-3" />
                    کپی صفحه
                  </button>
                  <button
                    onClick={() => handleExportPage(page.id)}
                    className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                  >
                    <Download className="w-3 h-3" />
                    خروجی JSON
                  </button>
                  {pages.length > 1 && (
                    <button
                      onClick={() => handleDeletePage(page.id)}
                      className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="w-3 h-3" />
                      حذف صفحه
                    </button>
                  )}
                </div>
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

        {/* Import page button */}
        <button
          onClick={handleImportPage}
          className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
          title="وارد کردن صفحه"
        >
          <Upload className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
