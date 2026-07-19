import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogout } from '../hooks/useLogout'
import {
  BarChart3, DollarSign, Users, Database, Upload, Settings, Zap,
  GitBranch, Briefcase, Package, FolderKanban, FileText,
  Shield, Bell, ArrowLeft, Check, Clock, Rocket, ChevronDown, ChevronUp
} from 'lucide-react'

interface RoadmapItem {
  id: string
  label: string
  labelEn: string
  description: string
  icon: React.ElementType
  status: 'implemented' | 'in-progress' | 'planned'
  category: string
  gradient: string
  route?: string
  features: string[]
}

const ROADMAP_ITEMS: RoadmapItem[] = [
  // Implemented modules
  {
    id: 'bi_dashboard',
    label: 'داشبورد هوشمند',
    labelEn: 'BI Dashboard',
    description: 'داشبوردهای تعاملی با نمودارها و فیلترهای پیشرفته',
    icon: BarChart3,
    status: 'implemented',
    category: 'هسته',
    gradient: 'from-indigo-500 to-purple-600',
    route: '/dashboards',
    features: [
      'کشیدن و رها کردن ویجت‌ها',
      'چند صفحه در هر داشبورد',
      '۱۵+ نوع نمودار (ECharts)',
      'فیلتر سطح داشبورد و ویجت',
      'فیلتر متقاطع نمودارها',
      'حفره‌ای (Drill-Down)',
      'امنیت سطح ردیف (RLS)',
      'یکپارچه‌سازی Superset',
    ],
  },
  {
    id: 'finance',
    label: 'حسابداری و مالی',
    labelEn: 'Finance',
    description: 'حسابداری ایرانی با استاندارد کل → معین → تفصیلی',
    icon: DollarSign,
    status: 'implemented',
    category: 'مالی',
    gradient: 'from-emerald-500 to-teal-600',
    route: '/finance',
    features: [
      'ساختار حساب: کل → معین → تفصیلی',
      'فاکتور با شماره‌گذاری خودکار',
      'رسید و پرداخت',
      'چک با چرخه عمر کامل',
      'سند حسابداری با اعتبارسنجی',
      'مشتری و تأمین‌کننده',
      'سال مالی و تراز افتتاحیه',
      'داشبورد KPI مالی',
    ],
  },
  {
    id: 'db_manager',
    label: 'مدیریت پایگاه داده',
    labelEn: 'Database Manager',
    description: 'اتصال، مرور، ویرایش و پرس‌وجوی پایگاه داده',
    icon: Database,
    status: 'implemented',
    category: 'داده',
    gradient: 'from-orange-500 to-amber-600',
    route: '/db-manager',
    features: [
      'اتصال به PostgreSQL, MySQL, SQL Server',
      'ویرایش مستقیم سلول‌ها',
      'ویرایشگر SQL',
      'ورود فایل Excel/CSV به جدول جدید',
      'همگام‌سازی Google Sheets',
      'رمزنگاری اطلاعات اتصال',
    ],
  },
  {
    id: 'datasets',
    label: 'بارگذاری داده',
    labelEn: 'Data Upload',
    description: 'آپلود و پردازش فایل‌های اکسل و CSV',
    icon: Upload,
    status: 'implemented',
    category: 'داده',
    gradient: 'from-pink-500 to-rose-600',
    route: '/data/upload',
    features: [
      'آپلود drag-and-drop',
      'پشتیبانی Excel (.xlsx/.xls) و CSV',
      'پردازش و پاکسازی خودکار',
      'ایجاد جدول PostgreSQL',
      ' Aggregate و GROUP BY',
    ],
  },
  {
    id: 'llm',
    label: 'دروازه هوش مصنوعی',
    labelEn: 'LLM Gateway',
    description: 'یکپارچه‌سازی چندین ارائه‌دهنده AI',
    icon: Zap,
    status: 'implemented',
    category: 'هوش مصنوعی',
    gradient: 'from-cyan-500 to-blue-600',
    route: '/settings/ai',
    features: [
      'پشتیبانی Ollama, OpenAI, Gemini, Anthropic',
      'رمزنگاری کلیدهای API',
      'محدودیت نرخ درخواست',
      'تاریخچه چت',
      'پیگیری مصرف توکن',
    ],
  },
  {
    id: 'settings',
    label: 'تنظیمات سازمان',
    labelEn: 'Settings',
    description: 'مدیریت ماژول‌ها، کاربران و ساختار سازمانی',
    icon: Settings,
    status: 'implemented',
    category: 'مدیریت',
    gradient: 'from-gray-500 to-slate-600',
    route: '/settings',
    features: [
      'فعال/غیرفعال کردن ماژول‌ها',
      'ساختار شرکت → بخش → تیم',
      'نمودار سازمانی',
      'نقش‌های سفارشی',
      'تخصیص دسته‌ای داشبورد',
    ],
  },

  // In-progress modules
  {
    id: 'crm',
    label: 'مدیریت ارتباط با مشتری',
    labelEn: 'CRM',
    description: 'ردیابی سرنخ‌ها، مدیریت خط لوله فروش و تاریخچه تماس',
    icon: Users,
    status: 'in-progress',
    category: 'روابط',
    gradient: 'from-violet-500 to-purple-600',
    features: [
      'پروفایل مشتری با جزئیات کامل',
      'ردیابی سرنخ (Lead Tracking)',
      'خط لوله فروش (Pipeline)',
      'تاریخچه تماس و تعاملات',
      'یادداشت‌ها و وظایف',
      'گزارش‌های فروش',
    ],
  },
  {
    id: 'workflows',
    label: 'گردش کار',
    labelEn: 'Workflows',
    description: 'زنجیره‌های تأیید سفارشی و خودکارسازی فرآیندها',
    icon: GitBranch,
    status: 'in-progress',
    category: 'خودکارسازی',
    gradient: 'from-amber-500 to-orange-600',
    features: [
      'طراحی گردش کار بصری',
      'زنجیره‌های تأیید چند سطحی',
      'اعلان‌ها و یادآوریها',
      'قانون‌گذاری شرطی',
      'گزارش وضعیت درخواست‌ها',
      'اتصال به ماژول‌های دیگر',
    ],
  },

  // Planned modules
  {
    id: 'hr',
    label: 'منابع انسانی',
    labelEn: 'HR',
    description: 'مدیریت کارکنان، حضور و غیاب، مرخصی و حقوق',
    icon: Briefcase,
    status: 'planned',
    category: 'سازمانی',
    gradient: 'from-teal-500 to-emerald-600',
    features: [
      'پرونده کارکنان',
      'حضور و غیاب',
      'درخواست مرخصی',
      'محاسبه حقوق و دستمزد',
      'ارزیابی عملکرد',
    ],
  },
  {
    id: 'inventory',
    label: 'مدیریت انبار',
    labelEn: 'Inventory',
    description: 'مدیریت موجودی، انبارها و سفارشات خرید',
    icon: Package,
    status: 'planned',
    category: 'عملیاتی',
    gradient: 'from-rose-500 to-pink-600',
    features: [
      'ردیابی موجودی',
      'چند انباره',
      'سفارش خرید',
      'بارکد و اسکنر',
      'هشدار کمبود موجودی',
    ],
  },
  {
    id: 'project',
    label: 'مدیریت پروژه',
    labelEn: 'Project',
    description: 'مدیریت وظایف، milestones و نمودار گانت',
    icon: FolderKanban,
    status: 'planned',
    category: 'عملیاتی',
    gradient: 'from-sky-500 to-indigo-600',
    features: [
      'تخته وظایف (Kanban)',
      'نمودار گانت',
      'زمان‌بندی پروژه',
      'گزارش پیشرفت',
      'تخصیص منابع',
    ],
  },
  {
    id: 'reports',
    label: 'گزارش‌ساز',
    labelEn: 'Reports',
    description: 'گزارش‌های زمان‌بندی شده با خروجی PDF و ایمیل',
    icon: FileText,
    status: 'planned',
    category: 'تحلیلی',
    gradient: 'from-lime-500 to-green-600',
    features: [
      'گزارش‌های زمان‌بندی شده',
      'خروجی PDF و Excel',
      'ارسال ایمیل',
      'قالب‌های آماده',
      'گزارش‌ساز بصری',
    ],
  },
  {
    id: 'audit',
    label: 'حسابرسی و انطباق',
    labelEn: 'Audit',
    description: 'ثبت تغییرات، ردیابی فعالیت و انطباق مقرراتی',
    icon: Shield,
    status: 'planned',
    category: 'امنیتی',
    gradient: 'from-red-500 to-rose-600',
    features: [
      'لاگ تغییرات (Audit Trail)',
      'ردیابی فعالیت کاربران',
      'گزارش انطباق',
      'هشدارهای امنیتی',
      'بازبینی دسترسی‌ها',
    ],
  },
  {
    id: 'notifications',
    label: 'سیستم اعلان',
    labelEn: 'Notifications',
    description: 'اعلان‌های ایمیل، SMS و درون‌برنامه‌ای',
    icon: Bell,
    status: 'planned',
    category: 'ارتباطی',
    gradient: 'from-fuchsia-500 to-purple-600',
    features: [
      'اعلان درون‌برنامه‌ای',
      'ایمیل و SMS',
      'وب‌هوک',
      'تنظیمات ترجیحی',
      'گروه‌بندی اعلان‌ها',
    ],
  },
]

const STATUS_CONFIG = {
  'implemented': {
    label: 'پیاده‌سازی شده',
    icon: Check,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/20 border-emerald-500/30',
    dot: 'bg-emerald-400',
  },
  'in-progress': {
    label: 'در حال توسعه',
    icon: Clock,
    color: 'text-amber-400',
    bg: 'bg-amber-500/20 border-amber-500/30',
    dot: 'bg-amber-400 animate-pulse',
  },
  'planned': {
    label: 'برنامه‌ریزی شده',
    icon: Rocket,
    color: 'text-gray-400',
    bg: 'bg-gray-500/20 border-gray-500/30',
    dot: 'bg-gray-400',
  },
}

const CATEGORIES = ['همه', ...Array.from(new Set(ROADMAP_ITEMS.map((i) => i.category)))]

export default function RoadmapPage() {
  const navigate = useNavigate()
  const handleLogout = useLogout()
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('همه')
  const [expandedItem, setExpandedItem] = useState<string | null>(null)

  const filteredItems = useMemo(
    () =>
      ROADMAP_ITEMS.filter((item) => {
        if (selectedStatus !== 'all' && item.status !== selectedStatus) return false
        if (selectedCategory !== 'همه' && item.category !== selectedCategory) return false
        return true
      }),
    [selectedStatus, selectedCategory]
  )

  const statusCounts = useMemo(
    () => ({
      implemented: ROADMAP_ITEMS.filter((i) => i.status === 'implemented').length,
      'in-progress': ROADMAP_ITEMS.filter((i) => i.status === 'in-progress').length,
      planned: ROADMAP_ITEMS.filter((i) => i.status === 'planned').length,
    }),
    []
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700/50 px-6 py-4 sticky top-0 z-10 bg-gray-900/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-xl transition"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-white">نقشه راه</h1>
              <p className="text-xs text-gray-400">Nexivo Roadmap</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-xl transition"
            title="خروج"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center">
                <Check className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{statusCounts.implemented}</p>
                <p className="text-xs text-gray-400">پیاده‌سازی شده</p>
              </div>
            </div>
            <div className="w-full bg-gray-700/50 rounded-full h-2 mt-3">
              <div
                className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(statusCounts.implemented / ROADMAP_ITEMS.length) * 100}%` }}
              />
            </div>
          </div>

          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-amber-500/20 rounded-xl flex items-center justify-center">
                <Clock className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{statusCounts['in-progress']}</p>
                <p className="text-xs text-gray-400">در حال توسعه</p>
              </div>
            </div>
            <div className="w-full bg-gray-700/50 rounded-full h-2 mt-3">
              <div
                className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(statusCounts['in-progress'] / ROADMAP_ITEMS.length) * 100}%` }}
              />
            </div>
          </div>

          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-gray-500/20 rounded-xl flex items-center justify-center">
                <Rocket className="w-5 h-5 text-gray-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{statusCounts.planned}</p>
                <p className="text-xs text-gray-400">برنامه‌ریزی شده</p>
              </div>
            </div>
            <div className="w-full bg-gray-700/50 rounded-full h-2 mt-3">
              <div
                className="bg-gray-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(statusCounts.planned / ROADMAP_ITEMS.length) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-8 space-y-4">
          {/* Status Filter */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedStatus('all')}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                selectedStatus === 'all'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
                  : 'bg-gray-800/50 text-gray-400 border border-gray-700/50 hover:border-gray-600'
              }`}
            >
              همه ({ROADMAP_ITEMS.length})
            </button>
            {(Object.entries(STATUS_CONFIG) as [string, typeof STATUS_CONFIG[keyof typeof STATUS_CONFIG]][]).map(
              ([key, config]) => (
                <button
                  key={key}
                  onClick={() => setSelectedStatus(key)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${
                    selectedStatus === key
                      ? `${config.bg} ${config.color} border`
                      : 'bg-gray-800/50 text-gray-400 border border-gray-700/50 hover:border-gray-600'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${config.dot}`} />
                  {config.label} ({statusCounts[key as keyof typeof statusCounts]})
                </button>
              )
            )}
          </div>

          {/* Category Filter */}
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedCategory === cat
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Roadmap Items */}
        <div className="space-y-4">
          {filteredItems.map((item) => {
            const statusConf = STATUS_CONFIG[item.status]
            const StatusIcon = statusConf.icon
            const isExpanded = expandedItem === item.id

            return (
              <div
                key={item.id}
                className={`bg-gray-800/50 border rounded-2xl overflow-hidden transition-all duration-300 ${
                  item.status === 'implemented'
                    ? 'border-gray-700/50 hover:border-emerald-500/30'
                    : item.status === 'in-progress'
                    ? 'border-amber-500/20 hover:border-amber-500/40'
                    : 'border-gray-700/30 hover:border-gray-600/50'
                }`}
              >
                <button
                  onClick={() => setExpandedItem(isExpanded ? null : item.id)}
                  className="w-full p-5 text-right flex items-center gap-4"
                >
                  {/* Icon */}
                  <div className={`w-12 h-12 bg-gradient-to-br ${item.gradient} rounded-xl flex items-center justify-center flex-shrink-0 ${
                    item.status === 'planned' ? 'opacity-60' : ''
                  }`}>
                    <item.icon className="w-6 h-6 text-white" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-bold text-white">{item.label}</h3>
                      <span className="text-xs text-gray-500 font-mono">{item.labelEn}</span>
                    </div>
                    <p className="text-sm text-gray-400 truncate">{item.description}</p>
                  </div>

                  {/* Status Badge */}
                  <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${statusConf.bg} ${statusConf.color} border flex-shrink-0`}>
                    <StatusIcon className="w-3.5 h-3.5" />
                    {statusConf.label}
                  </div>

                  {/* Category */}
                  <span className="text-xs text-gray-500 bg-gray-700/50 px-2.5 py-1 rounded-lg flex-shrink-0 hidden sm:block">
                    {item.category}
                  </span>

                  {/* Expand Arrow */}
                  <div className="text-gray-500 flex-shrink-0">
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </div>
                </button>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-5 pb-5 border-t border-gray-700/30">
                    <div className="pt-4">
                      <h4 className="text-sm font-semibold text-gray-300 mb-3">قابلیت‌ها</h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {item.features.map((feature, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 text-sm text-gray-400"
                          >
                            <div className={`w-1.5 h-1.5 rounded-full ${
                              item.status === 'implemented'
                                ? 'bg-emerald-400'
                                : item.status === 'in-progress'
                                ? 'bg-amber-400'
                                : 'bg-gray-500'
                            }`} />
                            {feature}
                          </div>
                        ))}
                      </div>

                      {item.route && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(item.route!)
                          }}
                          className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition flex items-center gap-2 w-fit"
                        >
                          <span>ورود به ماژول</span>
                          <ArrowLeft className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Empty State */}
        {filteredItems.length === 0 && (
          <div className="text-center py-16">
            <Rocket className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">ماژولی یافت نشد</p>
            <p className="text-gray-500 text-sm mt-2">فیلترها را تغییر دهید</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700/50 px-6 py-3 mt-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-500">
          <span>Nexivo v0.4.0 — Organization OS</span>
          <span>{ROADMAP_ITEMS.length} ماژول</span>
        </div>
      </footer>
    </div>
  )
}
