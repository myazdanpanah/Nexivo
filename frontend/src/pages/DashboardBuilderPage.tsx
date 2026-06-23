import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Responsive, WidthProvider } from 'react-grid-layout'
import { useDashboardStore, controlFiltersToQuery, type DashboardPageConfig, type DashboardFilterControl } from '../store/dashboardStore'
import api from '../api/client'
import ChartWidget from '../components/ChartWidget'
import WidgetConfigPanel from '../components/WidgetConfigPanel'
import DashboardFilterBar from '../components/DashboardFilterBar'
import PageNavBar from '../components/PageNavBar'
import { Plus, ArrowRight, Settings, Trash2 } from 'lucide-react'

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
  const [showConfig, setShowConfig] = useState(false)
  const [editingWidget, setEditingWidget] = useState<string | null>(null)
  const [mobileSettingsWidget, setMobileSettingsWidget] = useState<string | null>(null)
  const [isMobile, setIsMobile] = useState(false)
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

      // Load pages
      const serverPages: DashboardPageConfig[] = (res.data.pages || []).map((p: Record<string, unknown>) => ({
        id: String(p.id),
        name: p.name as string,
        order: p.order as number,
        layout: (p.layout as Array<Record<string, unknown>> || []).map((l) => ({
          i: String(l.i),
          x: l.x as number,
          y: l.y as number,
          w: l.w as number,
          h: l.h as number,
        })),
        filterControls: (p.filter_controls as DashboardFilterControl[]) || [],
        widgets: ((p.widgets as Array<Record<string, unknown>>) || []).map((w) => ({
          id: String(w.id),
          title: w.title as string,
          chartType: w.chart_type as string,
          datasetId: w.dataset as number | null,
          chartConfig: (w.chart_config as Record<string, unknown>) || {},
          queryConfig: (w.query_config as Record<string, unknown>) || {},
          columnTypes: (w.column_types as Record<string, string>) || {},
        })),
      }))

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
  const currentPageLayout = activePage?.layout || layout

  const handleLayoutChange = useCallback(
    (newLayout: Array<{ i: string; x: number; y: number; w: number; h: number }>) => {
      if (activePage && activePageId) {
        // Update page layout
        const { updatePage } = useDashboardStore.getState()
        updatePage(activePageId, { layout: newLayout })
      } else {
        setLayout(newLayout)
      }
      // Persist layout to backend
      if (id) {
        api.put(`/dashboards/${id}/layout/`, {
          layout: newLayout,
          page_id: activePageId || undefined,
        }).catch(() => {})
      }
    },
    [activePageId, id, setLayout]
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

  const deleteWidget = async (widgetId: string) => {
    if (!id) return
    try {
      await api.delete(`/dashboards/${id}/widgets/${widgetId}/`)
      removeWidget(widgetId)
      setShowConfig(false)
      setEditingWidget(null)
    } catch {
      // ignore
    }
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="max-w-full mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              to="/dashboards"
              className="p-2 text-gray-400 hover:text-gray-600 transition"
            >
              <ArrowRight className="w-5 h-5" />
            </Link>
            <h1 className="text-lg font-bold text-gray-900">ویرایشگر داشبورد</h1>
          </div>
          <div className="flex items-center gap-2">
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
            <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {activePage ? `${activePage.name} خالی است` : 'داشبورد خالی است'}
            </h3>
            <p className="text-gray-500 mb-6">
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
                <div key={w.id} className="group">
                  <div className={`bg-white border border-gray-200 h-full overflow-hidden ${shadow} hover:shadow-md transition`} style={{ borderRadius: radius }}>
                    <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
                      <span className="text-sm font-medium text-gray-700 truncate">
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
    </div>
  )
}
