import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Responsive, WidthProvider } from 'react-grid-layout'
import { useDashboardStore, controlFiltersToQuery, type DashboardPageConfig, type DashboardFilterControl } from '../store/dashboardStore'
import api from '../api/client'
import ChartWidget from '../components/ChartWidget'
import WidgetConfigPanel from '../components/WidgetConfigPanel'
import DashboardFilterBar from '../components/DashboardFilterBar'
import PageNavBar from '../components/PageNavBar'
import ThemeToggle from '../components/ThemeToggle'
import { useToast } from '../components/Toast'
import { Plus, ArrowRight, Settings, Trash2, Share2, X } from 'lucide-react'
import { ALL_ROLES } from '../utils/roles'

import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

const ResponsiveGridLayout = WidthProvider(Responsive)

export default function DashboardBuilderPage() {
  const { id } = useParams<{ id: string }>()
  const {
    pages, activePageId, setPages, setActivePage,
    layout, widgets, setLayout, setWidgets, addWidget, removeWidget,
    setDashboard, filters, setFilter, filterControls,
    setFilterControls,
  } = useDashboardStore()

  // Compute active control filters from filterControls state
  const controlFilters = controlFiltersToQuery(filterControls)

  // Load per-page filter controls when active page changes
  useEffect(() => {
    if (activePage) {
      setFilterControls(activePage.filterControls || [])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePageId])
  const { toast } = useToast()
  const [showConfig, setShowConfig] = useState(false)
  const [editingWidget, setEditingWidget] = useState<string | null>(null)
  const [mobileSettingsWidget, setMobileSettingsWidget] = useState<string | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  // Builder device mode: 'auto' follows viewport; 'desktop'/'mobile' force a layout for editing.
  const [deviceMode, setDeviceMode] = useState<'auto' | 'desktop' | 'mobile'>('auto')
  // Share modal state
  const [showShareModal, setShowShareModal] = useState(false)
  const [shareRoles, setShareRoles] = useState<string[]>([])
  // Drill-down state
  const [drillState, setDrillState] = useState<Record<string, Array<{ col: string; value: string }>>>({})

  useEffect(() => {
    if (id) loadDashboard(parseInt(id))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  // Detect mobile/tablet viewport
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const loadDashboard = async (dashboardId: number) => {
    try {
      const res = await api.get(`/dashboards/${dashboardId}/`)
      setDashboard(res.data.id, res.data.name)

      // Load persisted filter controls
      if (res.data.filter_controls) {
        setFilterControls(res.data.filter_controls)
      }

      // Load pages — build layout from raw server data before mapping widgets
      const serverPages: DashboardPageConfig[] = (res.data.pages || []).map((p: Record<string, unknown>) => {
        const rawWidgets = (p.widgets as Array<Record<string, unknown>>) || []
        let pageLayout = (p.layout as Array<Record<string, unknown>> || []).map((l) => ({
          i: String(l.i),
          x: l.x as number,
          y: l.y as number,
          w: l.w as number,
          h: l.h as number,
        }))

        // Backward compat: build layout from widget grid positions when layout is empty
        if (pageLayout.length === 0 && rawWidgets.length > 0) {
          pageLayout = rawWidgets.map((w) => ({
            i: String(w.id),
            x: (w.grid_x as number) ?? 0,
            y: (w.grid_y as number) ?? 0,
            w: (w.grid_w as number) ?? 6,
            h: (w.grid_h as number) ?? 4,
          }))
        }

        // Mobile layout: prefer persisted, else derive a stacked full-width grid
        // from the desktop layout (one widget per row, w=12).
        let mobileLayout = ((p.mobile_layout as Array<Record<string, unknown>>) || []).map((l) => ({
          i: String(l.i),
          x: l.x as number,
          y: l.y as number,
          w: l.w as number,
          h: l.h as number,
        }))
        if (mobileLayout.length === 0) {
          mobileLayout = pageLayout.map((l, idx) => ({ i: l.i, x: 0, y: idx, w: 12, h: l.h }))
        }

        return {
          id: String(p.id),
          name: p.name as string,
          order: p.order as number,
          layout: pageLayout,
          mobileLayout,
          filterControls: (p.filter_controls as DashboardFilterControl[]) || [],
          allowedRoles: (p.allowed_roles as string[]) || [],
          widgets: rawWidgets.map((w) => ({
            id: String(w.id),
            title: w.title as string,
            chartType: w.chart_type as string,
            datasetId: w.dataset as number | null,
            chartConfig: (w.chart_config as Record<string, unknown>) || {},
            queryConfig: (w.query_config as Record<string, unknown>) || {},
            columnTypes: (w.column_types as Record<string, string>) || {},
          })),
        }
      })

      if (serverPages.length > 0) {
        setPages(serverPages)
        setActivePage(serverPages[0].id)
      } else {
        // Legacy: widgets without pages
        const serverWidgets = (res.data.widgets || []).map((w: Record<string, unknown>) => ({
          id: String(w.id),
          title: w.title as string,
          chartType: w.chart_type as string,
          datasetId: w.dataset as number | null,
          chartConfig: (w.chart_config as Record<string, unknown>) || {},
          queryConfig: (w.query_config as Record<string, unknown>) || {},
          columnTypes: (w.column_types as Record<string, string>) || {},
        }))

        const serverLayout = (res.data.widgets || []).map((w: Record<string, unknown>) => ({
          i: String(w.id),
          x: w.grid_x as number,
          y: w.grid_y as number,
          w: w.grid_w as number,
          h: w.grid_h as number,
        }))

        setWidgets(serverWidgets)
        setLayout(serverLayout)
      }
    } catch {
      // ignore
    }
  }

  // Get active page data
  const activePage = pages.find((p) => p.id === activePageId)
  const currentPageWidgets = activePage?.widgets || widgets
  // Effective device: builder override beats viewport auto-detection.
  const editingMobile = deviceMode === 'mobile' || (deviceMode === 'auto' && isMobile)
  const desktopLayout = activePage?.layout || layout
  const mobileLayout = activePage?.mobileLayout || desktopLayout.map((l, idx) => ({ ...l, x: 0, y: idx, w: 12 }))
  const currentPageLayout = editingMobile ? mobileLayout : desktopLayout

  const handleLayoutChange = useCallback(
    (newLayout: Array<{ i: string; x: number; y: number; w: number; h: number }>) => {
      if (activePage && activePageId) {
        const { updatePage } = useDashboardStore.getState()
        if (editingMobile) {
          updatePage(activePageId, { mobileLayout: newLayout })
        } else {
          updatePage(activePageId, { layout: newLayout })
        }
      } else {
        setLayout(newLayout)
      }
      // Persist layout to backend
      if (id) {
        api.put(`/dashboards/${id}/layout/`, {
          layout: newLayout,
          page_id: activePageId || undefined,
          device: editingMobile ? 'mobile' : 'desktop',
        }).catch(() => {})
      }
    },
    [activePageId, id, setLayout, editingMobile]
  )

  const addNewWidget = async () => {
    if (!id) return
    try {
      const payload: Record<string, unknown> = {
        title: 'نمودار جدید',
        chart_type: 'bar',
        chart_config: {},
        query_config: {},
        grid_x: 0,
        grid_y: 0,
        grid_w: 6,
        grid_h: 4,
      }
      // Assign widget to active page
      if (activePageId) {
        payload.page = parseInt(activePageId)
      }
      const res = await api.post(`/dashboards/${id}/widgets/`, payload)
      addWidget({
        id: String(res.data.id),
        title: res.data.title,
        chartType: res.data.chart_type,
        datasetId: res.data.dataset,
        chartConfig: res.data.chart_config,
        queryConfig: res.data.query_config,
      })
      setEditingWidget(String(res.data.id))
      setShowConfig(true)
    } catch {
      // ignore
    }
  }

  const openShareModal = async () => {
    if (!id) return
    try {
      const res = await api.get(`/dashboards/${id}/`)
      setShareRoles(res.data.allowed_roles || [])
      setShowShareModal(true)
    } catch {
      toast('خطا در دریافت اطلاعات', 'error')
    }
  }

  const handleShareSave = async () => {
    if (!id) return
    try {
      await api.put(`/dashboards/${id}/share/`, { allowed_roles: shareRoles })
      setShowShareModal(false)
      toast('دسترسی‌ها به‌روز شد', 'success')
    } catch {
      toast('خطا در به‌روزرسانی دسترسی‌ها', 'error')
    }
  }

  const deleteWidget = async (widgetId: string) => {
    if (!id) return
    if (!window.confirm('آیا از حذف این نمودار اطمینان دارید؟')) return
    try {
      await api.delete(`/dashboards/${id}/widgets/${widgetId}/`)
      removeWidget(widgetId)
      setShowConfig(false)
      setEditingWidget(null)
      toast('نمودار حذف شد', 'success')
    } catch {
      toast('خطا در حذف نمودار', 'error')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900" dir="rtl">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="max-w-full mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              to="/dashboards"
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
            >
              <ArrowRight className="w-5 h-5" />
            </Link>
            <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">ویرایشگر داشبورد</h1>
            {/* Device mode toggle (Desktop / Mobile builder) */}
            <div className="flex items-center gap-1 mr-2 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
              {(['desktop', 'mobile'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setDeviceMode(mode)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                    deviceMode === mode
                      ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-300 shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                  }`}
                  title={mode === 'mobile' ? 'ویرایش چیدمان موبایل' : 'ویرایش چیدمان دسکتاپ'}
                >
                  {mode === 'mobile' ? '📱 موبایل' : '🖥️ دسکتاپ'}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={openShareModal}
              className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition text-sm"
              title="اشتراک‌گذاری و دسترسی"
            >
              <Share2 className="w-4 h-4" />
              اشتراک‌گذاری
            </button>
            <button
              onClick={addNewWidget}
              className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm"
            >
              <Plus className="w-4 h-4" />
              افزودن نمودار
            </button>
          </div>
        </div>
      </header>

      {/* Page Navigation Bar */}
      <PageNavBar />

      {/* Dashboard-level Filter Bar */}
      {currentPageWidgets.length > 0 && <DashboardFilterBar />}

      {/* Dashboard Grid */}
      <main className="p-6">
        {currentPageWidgets.length === 0 ? (
          <div className="text-center py-20">
            <Settings className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              {activePage ? `${activePage.name} خالی است` : 'داشبورد خالی است'}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              اولین نمودار خود را اضافه کنید
            </p>
            <button
              onClick={addNewWidget}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition font-medium"
            >
              افزودن نمودار
            </button>
          </div>
        ) : (
          <div className="react-grid-layout-wrapper">
            <ResponsiveGridLayout
              className="layout"
              layouts={{ lg: currentPageLayout, md: currentPageLayout, sm: currentPageLayout }}
              breakpoints={{ lg: 1200, md: 996, sm: 768 }}
              cols={{ lg: 12, md: 9, sm: 6 }}
              rowHeight={60}
              onLayoutChange={handleLayoutChange}
              isDraggable
              isResizable
              useCSSTransforms
              compactType="vertical"
              draggableHandle={isMobile ? '.drag-handle' : undefined}
            >
              {currentPageWidgets.map((w) => {
                const ws = (w.chartConfig as Record<string, unknown>)?.widgetStyle as { shadow?: string; borderRadius?: number } | undefined
                const shadow = ws?.shadow === 'none' ? '' : ws?.shadow === 'md' ? 'shadow-md' : ws?.shadow === 'lg' ? 'shadow-lg' : 'shadow-sm'
                const radius = ws?.borderRadius ?? 16
                return (
                  <div key={w.id} className="group" style={{ direction: 'rtl', textAlign: 'right' }}>
                    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 h-full overflow-hidden ${shadow} hover:shadow-md transition`} style={{ borderRadius: radius }}>
                      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">
                          {w.title}
                        </span>
                        <div className="flex items-center gap-1">
                          {!isMobile ? (
                            <>
                              <button
                                onClick={() => {
                                  setEditingWidget(w.id)
                                  setShowConfig(true)
                                }}
                                className="p-1 text-gray-400 hover:text-indigo-500 transition opacity-0 group-hover:opacity-100"
                              >
                                <Settings className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => deleteWidget(w.id)}
                                className="p-1 text-gray-400 hover:text-red-500 transition opacity-0 group-hover:opacity-100"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </>
                          ) : (
                            <>
                              <div className="drag-handle p-1 text-gray-400 cursor-grab active:cursor-grabbing">
                                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="9" cy="5" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="9" cy="19" r="1"/><circle cx="15" cy="19" r="1"/></svg>
                              </div>
                              <button
                                onClick={() => setMobileSettingsWidget(w.id)}
                                className="p-1 text-gray-500 active:text-indigo-600"
                              >
                                <Settings className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteWidget(w.id)}
                                className="p-1 text-gray-500 active:text-red-500"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="p-2" style={{ height: 'calc(100% - 40px)' }}>
                        <ChartWidget
                          widget={w}
                          dashboardFilters={filters}
                          dashboardControlFilters={controlFilters}
                          onFilter={setFilter}
                          drillBreadcrumb={drillState[w.id] || []}
                          onDrillDown={(col, value) => {
                            setDrillState((prev) => ({
                              ...prev,
                              [w.id]: [...(prev[w.id] || []), { col, value }],
                            }))
                          }}
                          onDrillUp={(index) => {
                            setDrillState((prev) => ({
                              ...prev,
                              [w.id]: (prev[w.id] || []).slice(0, index + 1),
                            }))
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </ResponsiveGridLayout>
          </div>
        )}
      </main>

      {/* Widget Config Panel (desktop) */}
      {showConfig && editingWidget && !isMobile && (
        <WidgetConfigPanel
          widgetId={editingWidget}
          onClose={() => {
            setShowConfig(false)
            setEditingWidget(null)
          }}
        />
      )}

      {/* Mobile Settings Modal — full panel, same as desktop */}
      {mobileSettingsWidget && isMobile && (
        <WidgetConfigPanel
          widgetId={mobileSettingsWidget}
          onClose={() => setMobileSettingsWidget(null)}
        />
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" dir="rtl">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowShareModal(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h3 className="font-bold text-gray-900 dark:text-gray-100">اشتراک‌گذاری و دسترسی</h3>
              <button onClick={() => setShowShareModal(false)} className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">نقش‌هایی که به این داشبورد دسترسی دارند:</p>
              <div className="space-y-2">
                {ALL_ROLES.map((r) => (
                  <label
                    key={r.value}
                    className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition"
                  >
                    <input
                      type="checkbox"
                      checked={shareRoles.includes(r.value)}
                      onChange={() => setShareRoles((prev) => prev.includes(r.value) ? prev.filter((v) => v !== r.value) : [...prev, r.value])}
                      className="w-4 h-4 text-indigo-600 rounded border-gray-300 dark:border-gray-500 focus:ring-indigo-500"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{r.label}</span>
                  </label>
                ))}
              </div>
              <p className="text-[10px] text-gray-400 mt-3">بدون انتخاب = همه نقش‌ها مجازند</p>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowShareModal(false)}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition"
              >
                انصراف
              </button>
              <button
                onClick={handleShareSave}
                className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-xl hover:bg-indigo-700 transition font-medium"
              >
                ذخیره دسترسی‌ها
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
