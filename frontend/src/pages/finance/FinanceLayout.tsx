import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import {
  LayoutDashboard, BookOpen, FileText, Receipt,
  CreditCard, Landmark, Users, Truck, ChevronLeft,
  LogOut, Zap, Calculator
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/finance', icon: LayoutDashboard, label: 'داشبورد', end: true },
  { to: '/finance/chart-of-accounts', icon: BookOpen, label: 'حساب‌ها' },
  { to: '/finance/invoices', icon: FileText, label: 'فاکتورها' },
  { to: '/finance/receipts', icon: Receipt, label: 'دریافت‌ها' },
  { to: '/finance/payments', icon: CreditCard, label: 'پرداخت‌ها' },
  { to: '/finance/cheques', icon: Landmark, label: 'چک‌ها' },
  { to: '/finance/customers', icon: Users, label: 'مشتریان' },
  { to: '/finance/suppliers', icon: Truck, label: 'تأمین‌کنندگان' },
  { to: '/finance/vouchers', icon: Calculator, label: 'اسناد حسابداری' },
]

export default function FinanceLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-950 flex" dir="rtl">
      {/* Sidebar */}
      <aside
        className={`${
          collapsed ? 'w-16' : 'w-60'
        } bg-gray-900 border-l border-gray-800 flex flex-col transition-all duration-300`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">مدیریت مالی</h2>
                <p className="text-[10px] text-gray-500">Finance Module</p>
              </div>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition"
          >
            <ChevronLeft
              className={`w-4 h-4 transition-transform ${collapsed ? 'rotate-180' : ''}`}
            />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                } ${collapsed ? 'justify-center' : ''}`
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-gray-800">
          {!collapsed && (
            <div className="text-xs text-gray-500 mb-2 px-2 truncate">
              {user?.username}
            </div>
          )}
          <button
            onClick={handleLogout}
            className={`w-full flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-red-400 hover:bg-gray-800/50 rounded-xl transition text-sm ${
              collapsed ? 'justify-center' : ''
            }`}
          >
            <LogOut className="w-4 h-4" />
            {!collapsed && <span>خروج</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
