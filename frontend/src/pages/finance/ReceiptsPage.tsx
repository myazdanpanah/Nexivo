import { useState, useEffect } from 'react'
import { getReceipts, createReceipt, deleteReceipt, getCustomers, getBankAccounts } from '../../api/finance'
import { useToast } from '../../components/Toast'
import { Plus, Receipt, Trash2 } from 'lucide-react'

interface ReceiptItem {
  id: number
  number: number
  date_jalali: string
  customer_name: string
  bank_account_name: string
  amount: number
  payment_method: string
  reference: string
  description: string
  status: string
  created_at: string
}

const PAYMENT_METHODS: Record<string, string> = {
  cash: 'نقدی',
  bank_transfer: 'انتقال بانکی',
  cheque: 'چک',
  pos: 'کارت خوان',
  online: 'پرداخت آنلاین',
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'پیش‌نویس',
  confirmed: 'تأیید شده',
  cancelled: 'لغو شده',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  confirmed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  cancelled: 'bg-red-500/10 text-red-400 border-red-500/20',
}

const formatIRR = (n: number) => new Intl.NumberFormat('fa-IR').format(n) + ' ریال'

interface Party { id: number; name: string }
interface Bank { id: number; name: string }

export default function ReceiptsPage() {
  const { toast } = useToast()
  const [receipts, setReceipts] = useState<ReceiptItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [customers, setCustomers] = useState<Party[]>([])
  const [banks, setBanks] = useState<Bank[]>([])
  const [form, setForm] = useState({
    date_jalali: '',
    customer: '',
    bank_account: '',
    amount: '',
    payment_method: 'cash',
    reference: '',
    description: '',
  })

  useEffect(() => { fetchAll() }, [])

  const fetchAll = async () => {
    try {
      const [rRes, cRes, bRes] = await Promise.all([
        getReceipts(), getCustomers(), getBankAccounts(),
      ])
      setReceipts(rRes.data)
      setCustomers(cRes.data)
      setBanks(bRes.data)
    } catch {
      toast('خطا در دریافت اطلاعات', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!form.customer || !form.bank_account || !form.amount) {
      toast('لطفاً فیلدهای ضروری را پر کنید', 'error')
      return
    }
    try {
      await createReceipt({
        ...form,
        amount: Number(form.amount),
        date: new Date().toISOString().split('T')[0],
        status: 'draft',
      })
      toast('رسید دریافت ایجاد شد', 'success')
      setShowCreate(false)
      setForm({ date_jalali: '', customer: '', bank_account: '', amount: '', payment_method: 'cash', reference: '', description: '' })
      fetchAll()
    } catch {
      toast('خطا در ایجاد رسید', 'error')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('آیا از حذف مطمئن هستید؟')) return
    try {
      await deleteReceipt(id)
      toast('رسید حذف شد', 'success')
      fetchAll()
    } catch {
      toast('خطا در حذف', 'error')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">دریافت‌ها (واریزی)</h1>
          <p className="text-gray-400 mt-1">{receipts.length} رسید</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition"
        >
          <Plus className="w-4 h-4" />
          رسید جدید
        </button>
      </div>

      {receipts.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <Receipt className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <p className="text-lg">هنوز رسیدی ثبت نشده</p>
        </div>
      ) : (
        <div className="space-y-3">
          {receipts.map(r => (
            <div key={r.id} className="bg-gray-900/50 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-all flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <Receipt className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <span className="text-white font-bold">رسید شماره {r.number}</span>
                  <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[r.status] || ''}`}>
                    {STATUS_LABELS[r.status]}
                  </span>
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  {r.date_jalali} — {r.customer_name} — {r.bank_account_name}
                  {r.reference && <span className="mr-2">({r.reference})</span>}
                </div>
              </div>
              <div className="text-left">
                <p className="text-emerald-400 font-bold text-lg">{formatIRR(r.amount)}</p>
                <p className="text-xs text-gray-500">{PAYMENT_METHODS[r.payment_method]}</p>
              </div>
              <button
                onClick={() => handleDelete(r.id)}
                className="p-2 text-gray-500 hover:text-red-400 transition"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg p-6" dir="rtl">
            <h2 className="text-xl font-bold text-white mb-6">رسید دریافت جدید</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">تاریخ</label>
                  <input
                    type="text"
                    value={form.date_jalali}
                    onChange={e => setForm(f => ({ ...f, date_jalali: e.target.value }))}
                    placeholder="۱۴۰۴/۰۴/۲۵"
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">مبلغ (ریال)</label>
                  <input
                    type="number"
                    value={form.amount}
                    onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">مشتری</label>
                <select
                  value={form.customer}
                  onChange={e => setForm(f => ({ ...f, customer: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="">انتخاب مشتری...</option>
                  {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">حساب بانکی</label>
                <select
                  value={form.bank_account}
                  onChange={e => setForm(f => ({ ...f, bank_account: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="">انتخاب حساب...</option>
                  {banks.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">روش پرداخت</label>
                <select
                  value={form.payment_method}
                  onChange={e => setForm(f => ({ ...f, payment_method: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  {Object.entries(PAYMENT_METHODS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">مرجع</label>
                  <input
                    type="text"
                    value={form.reference}
                    onChange={e => setForm(f => ({ ...f, reference: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">توضیحات</label>
                  <input
                    type="text"
                    value={form.description}
                    onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button onClick={handleCreate} className="flex-1 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition">
                  ایجاد رسید
                </button>
                <button onClick={() => setShowCreate(false)} className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl transition">
                  انصراف
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
