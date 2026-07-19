import { useState, useEffect } from 'react'
import { getCheques, createCheque, updateCheque, deleteCheque } from '../../api/finance'
import { useToast } from '../../components/Toast'
import { Plus, Landmark, Trash2, Check } from 'lucide-react'

interface ChequeItem {
  id: number
  cheque_type: string
  number: string
  bank_name: string
  branch_name: string
  amount: number
  issue_date_jalali: string
  due_date_jalali: string
  customer_name: string | null
  supplier_name: string | null
  status: string
  description: string
}

const TYPE_LABELS: Record<string, string> = { received: 'دریافتی', issued: 'صادره' }
const STATUS_LABELS: Record<string, string> = { pending: 'در انتظار', passed: 'وصول شده', bounced: 'برگشتی', cancelled: 'لغو شده' }
const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  passed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  bounced: 'bg-red-500/10 text-red-400 border-red-500/20',
  cancelled: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
}
const TYPE_COLORS: Record<string, string> = {
  received: 'from-blue-500 to-cyan-600',
  issued: 'from-amber-500 to-orange-600',
}

const formatIRR = (n: number) => new Intl.NumberFormat('fa-IR').format(n) + ' ریال'

export default function ChequesPage() {
  const { toast } = useToast()
  const [cheques, setCheques] = useState<ChequeItem[]>([])
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    cheque_type: 'received',
    number: '',
    bank_name: '',
    branch_name: '',
    amount: '',
    issue_date_jalali: '',
    due_date_jalali: '',
    description: '',
  })

  useEffect(() => { fetchCheques() }, [typeFilter])

  const fetchCheques = async () => {
    try {
      const params: Record<string, string> = {}
      if (typeFilter) params.cheque_type = typeFilter
      const res = await getCheques(params)
      setCheques(res.data)
    } catch {
      toast('خطا در دریافت چک‌ها', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!form.number || !form.bank_name || !form.amount || !form.issue_date_jalali || !form.due_date_jalali) {
      toast('لطفاً فیلدهای ضروری را پر کنید', 'error')
      return
    }
    try {
      await createCheque({
        ...form,
        amount: Number(form.amount),
        issue_date: new Date().toISOString().split('T')[0],
        due_date: new Date().toISOString().split('T')[0],
        status: 'pending',
      })
      toast('چک ایجاد شد', 'success')
      setShowCreate(false)
      fetchCheques()
    } catch {
      toast('خطا در ایجاد چک', 'error')
    }
  }

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await updateCheque(id, { status: newStatus })
      toast('وضعیت چک به‌روز شد', 'success')
      fetchCheques()
    } catch {
      toast('خطا در به‌روزرسانی', 'error')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('آیا از حذف مطمئن هستید؟')) return
    try {
      await deleteCheque(id)
      toast('چک حذف شد', 'success')
      fetchCheques()
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
          <h1 className="text-2xl font-bold text-white">چک‌ها</h1>
          <p className="text-gray-400 mt-1">{cheques.length} چک</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition">
          <Plus className="w-4 h-4" />
          چک جدید
        </button>
      </div>

      <div className="flex items-center gap-2">
        {['', 'received', 'issued'].map(t => (
          <button key={t} onClick={() => setTypeFilter(t)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              typeFilter === t ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-gray-800/50 text-gray-400 hover:text-white border border-transparent'
            }`}>
            {t ? TYPE_LABELS[t] : 'همه'}
          </button>
        ))}
      </div>

      {cheques.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <Landmark className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <p className="text-lg">هنوز چکی ثبت نشده</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {cheques.map(ch => (
            <div key={ch.id} className="bg-gray-900/50 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-all">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 bg-gradient-to-br ${TYPE_COLORS[ch.cheque_type]} rounded-xl flex items-center justify-center`}>
                    <Landmark className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-white font-bold">چک شماره {ch.number}</h3>
                    <span className="text-xs text-gray-400">{ch.bank_name} {ch.branch_name}</span>
                  </div>
                </div>
                <span className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${STATUS_COLORS[ch.status] || ''}`}>
                  {STATUS_LABELS[ch.status]}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-gray-500">نوع:</span> <span className="text-white">{TYPE_LABELS[ch.cheque_type]}</span></div>
                <div><span className="text-gray-500">مبلغ:</span> <span className="text-emerald-400 font-bold">{formatIRR(ch.amount)}</span></div>
                <div><span className="text-gray-500">تاریخ صدور:</span> <span className="text-white">{ch.issue_date_jalali}</span></div>
                <div><span className="text-gray-500">سررسید:</span> <span className="text-white">{ch.due_date_jalali}</span></div>
                {ch.customer_name && <div><span className="text-gray-500">مشتری:</span> <span className="text-white">{ch.customer_name}</span></div>}
                {ch.supplier_name && <div><span className="text-gray-500">تأمین‌کننده:</span> <span className="text-white">{ch.supplier_name}</span></div>}
              </div>
              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-800">
                {ch.status === 'pending' && (
                  <>
                    <button onClick={() => handleStatusChange(ch.id, 'passed')}
                      className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-500/20 transition">
                      <Check className="w-3.5 h-3.5" /> وصول
                    </button>
                    <button onClick={() => handleStatusChange(ch.id, 'bounced')}
                      className="flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/20 transition">
                      برگشت
                    </button>
                  </>
                )}
                <button onClick={() => handleDelete(ch.id)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/20 transition mr-auto">
                  <Trash2 className="w-3.5 h-3.5" /> حذف
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg p-6" dir="rtl">
            <h2 className="text-xl font-bold text-white mb-6">چک جدید</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">نوع چک</label>
                  <select value={form.cheque_type} onChange={e => setForm(f => ({ ...f, cheque_type: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500">
                    {Object.entries(TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">شماره چک</label>
                  <input type="text" value={form.number} onChange={e => setForm(f => ({ ...f, number: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">بانک</label>
                  <input type="text" value={form.bank_name} onChange={e => setForm(f => ({ ...f, bank_name: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">شعبه</label>
                  <input type="text" value={form.branch_name} onChange={e => setForm(f => ({ ...f, branch_name: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">مبلغ (ریال)</label>
                <input type="number" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">تاریخ صدور</label>
                  <input type="text" value={form.issue_date_jalali} onChange={e => setForm(f => ({ ...f, issue_date_jalali: e.target.value }))} placeholder="۱۴۰۴/۰۴/۲۵"
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">تاریخ سررسید</label>
                  <input type="text" value={form.due_date_jalali} onChange={e => setForm(f => ({ ...f, due_date_jalali: e.target.value }))} placeholder="۱۴۰۴/۰۷/۲۵"
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">توضیحات</label>
                <input type="text" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button onClick={handleCreate} className="flex-1 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition">
                  ایجاد چک
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
