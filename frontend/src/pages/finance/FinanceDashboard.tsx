import { useState, useEffect } from 'react'
import { getFinanceSummary } from '../../api/finance'
import { useToast } from '../../components/Toast'
import {
  TrendingUp, TrendingDown, Landmark, Users, Truck,
  Receipt, CreditCard, FileText, Calendar
} from 'lucide-react'

interface FinanceSummary {
  fiscal_year: { name: string; start_date_jalali: string; end_date_jalali: string } | null
  total_sales: number
  total_purchases: number
  total_receipts: number
  total_payments: number
  open_cheques_received: number
  open_cheques_issued: number
  bank_balance: number
  customers_count: number
  suppliers_count: number
}

const formatIRR = (amount: number) => {
  return new Intl.NumberFormat('fa-IR').format(amount) + ' ریال'
}

const KPICard = ({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType
  label: string
  value: string | number
  color: string
}) => (
  <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-all duration-200">
    <div className="flex items-start justify-between mb-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
    </div>
    <p className="text-2xl font-bold text-white mb-1">{value}</p>
    <p className="text-sm text-gray-400">{label}</p>
  </div>
)

export default function FinanceDashboard() {
  const { toast } = useToast()
  const [summary, setSummary] = useState<FinanceSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSummary()
  }, [])

  const fetchSummary = async () => {
    try {
      const res = await getFinanceSummary()
      setSummary(res.data)
    } catch {
      toast('خطا در دریافت خلاصه مالی', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-500">
        خلاصه مالی در دسترس نیست
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">داشبورد مالی</h1>
          <p className="text-gray-400 mt-1">
            {summary.fiscal_year
              ? `سال مالی ${summary.fiscal_year.name}`
              : 'سال مالی تعریف نشده'}
          </p>
        </div>
        {summary.fiscal_year && (
          <div className="flex items-center gap-2 text-sm text-gray-400 bg-gray-800/50 px-4 py-2 rounded-xl">
            <Calendar className="w-4 h-4" />
            <span>
              {summary.fiscal_year.start_date_jalali} — {summary.fiscal_year.end_date_jalali}
            </span>
          </div>
        )}
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          icon={TrendingUp}
          label="فروش تأیید شده"
          value={formatIRR(summary.total_sales)}
          color="bg-gradient-to-br from-emerald-500 to-teal-600"
        />
        <KPICard
          icon={TrendingDown}
          label="خرید تأیید شده"
          value={formatIRR(summary.total_purchases)}
          color="bg-gradient-to-br from-orange-500 to-amber-600"
        />
        <KPICard
          icon={Receipt}
          label="دریافت‌ها"
          value={formatIRR(summary.total_receipts)}
          color="bg-gradient-to-br from-blue-500 to-cyan-600"
        />
        <KPICard
          icon={CreditCard}
          label="پرداخت‌ها"
          value={formatIRR(summary.total_payments)}
          color="bg-gradient-to-br from-rose-500 to-pink-600"
        />
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          icon={Landmark}
          label="مانده بانک"
          value={formatIRR(summary.bank_balance)}
          color="bg-gradient-to-br from-indigo-500 to-purple-600"
        />
        <KPICard
          icon={FileText}
          label="چک‌های دریافتی (باز)"
          value={formatIRR(summary.open_cheques_received)}
          color="bg-gradient-to-br from-emerald-500 to-green-600"
        />
        <KPICard
          icon={FileText}
          label="چک‌های صادره (باز)"
          value={formatIRR(summary.open_cheques_issued)}
          color="bg-gradient-to-br from-amber-500 to-yellow-600"
        />
        <KPICard
          icon={Users}
          label="مشتریان فعال"
          value={summary.customers_count}
          color="bg-gradient-to-br from-cyan-500 to-blue-600"
        />
      </div>

      {/* Bottom Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">مانده حساب‌ها</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-xl">
              <span className="text-gray-300">مانده بانک</span>
              <span className="text-white font-medium">{formatIRR(summary.bank_balance)}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-xl">
              <span className="text-gray-300">دریافتی‌ها - پرداختی‌ها</span>
              <span className={`font-medium ${summary.total_receipts - summary.total_payments >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {formatIRR(summary.total_receipts - summary.total_payments)}
              </span>
            </div>
          </div>
        </div>
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">آمار طرف حساب‌ها</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-xl">
              <Users className="w-5 h-5 text-cyan-400" />
              <span className="text-gray-300 flex-1">مشتریان فعال</span>
              <span className="text-white font-bold text-lg">{summary.customers_count}</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-xl">
              <Truck className="w-5 h-5 text-amber-400" />
              <span className="text-gray-300 flex-1">تأمین‌کنندگان فعال</span>
              <span className="text-white font-bold text-lg">{summary.suppliers_count}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
