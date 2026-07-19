import { useState, useEffect } from 'react'
import { getVouchers, createVoucher, confirmVoucher, deleteVoucher, getKolAccounts, getFiscalYears } from '../../api/finance'
import { useToast } from '../../components/Toast'
import { Plus, Calculator, Check, Trash2, ChevronDown, ChevronRight } from 'lucide-react'

interface JournalEntry {
  id: number
  kol: number
  kol_name: string
  moin_name: string | null
  tafzili_name: string | null
  description: string
  debit: number
  credit: number
}

interface VoucherItem {
  id: number
  number: number
  date_jalali: string
  description: string
  status: string
  total_debit: number
  total_credit: number
  entries: JournalEntry[]
  created_by_name: string
  created_at: string
}

interface KolAccount {
  id: number
  code: string
  name: string
}

interface FiscalYearItem {
  id: number
  name: string
  is_closed: boolean
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
const formatIRR = (n: number) => new Intl.NumberFormat('fa-IR').format(n)

export default function VouchersPage() {
  const { toast } = useToast()
  const [vouchers, setVouchers] = useState<VoucherItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [kolAccounts, setKolAccounts] = useState<KolAccount[]>([])
  const [fiscalYears, setFiscalYears] = useState<FiscalYearItem[]>([])
  const [selectedFY, setSelectedFY] = useState<string>('')

  const [form, setForm] = useState({
    date_jalali: '',
    description: '',
    entries: [
      { kol: '', moin: '', tafzili: '', description: '', debit: '', credit: '' },
      { kol: '', moin: '', tafzili: '', description: '', debit: '', credit: '' },
    ] as Array<{ kol: string; moin: string; tafzili: string; description: string; debit: string; credit: string }>,
  })

  useEffect(() => { fetchKols(); fetchFiscalYears() }, [])
  useEffect(() => { fetchVouchers() }, [selectedFY])

  const fetchVouchers = async () => {
    try {
      const params: Record<string, unknown> = {}
      if (selectedFY) params.fiscal_year = selectedFY
      const res = await getVouchers(params)
      setVouchers(res.data)
    } catch {
      toast('خطا در دریافت اسناد', 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchKols = async () => {
    try {
      const res = await getKolAccounts()
      setKolAccounts(res.data)
    } catch { /* silent */ }
  }

  const fetchFiscalYears = async () => {
    try {
      const res = await getFiscalYears()
      setFiscalYears(res.data)
      const open = res.data.find((f: FiscalYearItem) => !f.is_closed)
      if (open) setSelectedFY(String(open.id))
    } catch { /* silent */ }
  }

  const handleConfirm = async (id: number) => {
    try {
      await confirmVoucher(id)
      toast('سند تأیید شد', 'success')
      fetchVouchers()
    } catch {
      toast('خطا در تأیید سند — بدهکار و بستانکار باید برابر باشند', 'error')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('آیا از حذف این سند مطمئن هستید؟')) return
    try {
      await deleteVoucher(id)
      toast('سند حذف شد', 'success')
      fetchVouchers()
    } catch {
      toast('خطا در حذف', 'error')
    }
  }

  const handleCreate = async () => {
    const today = new Date().toISOString().split('T')[0]
    const todayJalali = new Date().toLocaleDateString('fa-IR')
    const totalDebit = form.entries.reduce((s, e) => s + (Number(e.debit) || 0), 0)
    const totalCredit = form.entries.reduce((s, e) => s + (Number(e.credit) || 0), 0)

    if (totalDebit !== totalCredit || totalDebit === 0) {
      toast('جمع بدهکار و بستانکار باید برابر و غیرصفر باشد', 'error')
      return
    }

    try {
      await createVoucher({
        date_jalali: form.date_jalali || todayJalali,
        date: today,
        description: form.description,
        source_type: 'manual',
        fiscal_year: selectedFY || undefined,
        entries: form.entries
          .filter(e => e.kol)
          .map(e => ({
            kol: Number(e.kol),
            moin: e.moin ? Number(e.moin) : null,
            tafzili: e.tafzili ? Number(e.tafzili) : null,
            description: e.description,
            debit: Number(e.debit) || 0,
            credit: Number(e.credit) || 0,
          })),
      })
      toast('سند ایجاد شد', 'success')
      setShowCreate(false)
      fetchVouchers()
    } catch {
      toast('خطا در ایجاد سند', 'error')
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
          <h1 className="text-2xl font-bold text-white">اسناد حسابداری</h1>
          <p className="text-gray-400 mt-1">{vouchers.length} سند</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition">
          <Plus className="w-4 h-4" />
          سند جدید
        </button>
      </div>

      {vouchers.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <Calculator className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <p className="text-lg">هنوز سندی ثبت نشده</p>
        </div>
      ) : (
        <div className="space-y-3">
          {vouchers.map(v => (
            <div key={v.id} className="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden hover:border-gray-700 transition-all">
              <button
                onClick={() => setExpandedId(expandedId === v.id ? null : v.id)}
                className="w-full flex items-center gap-4 px-5 py-4 text-right"
              >
                {expandedId === v.id
                  ? <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  : <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                }
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-white font-bold">سند شماره {v.number}</span>
                    <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[v.status] || ''}`}>
                      {STATUS_LABELS[v.status]}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    {v.date_jalali} — {v.description}
                  </div>
                </div>
                <div className="text-left space-y-1">
                  <div className="text-sm">
                    <span className="text-gray-500">بدهکار: </span>
                    <span className="text-emerald-400 font-bold">{formatIRR(v.total_debit)}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-500">بستانکار: </span>
                    <span className="text-blue-400 font-bold">{formatIRR(v.total_credit)}</span>
                  </div>
                </div>
              </button>

              {/* Expanded entries */}
              {expandedId === v.id && (
                <div className="border-t border-gray-800 px-5 py-4">
                  <div className="bg-gray-800/50 rounded-xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-700">
                          <th className="px-4 py-2 text-right text-gray-400 font-medium">حساب</th>
                          <th className="px-4 py-2 text-right text-gray-400 font-medium">شرح</th>
                          <th className="px-4 py-2 text-left text-gray-400 font-medium">بدهکار</th>
                          <th className="px-4 py-2 text-left text-gray-400 font-medium">بستانکار</th>
                        </tr>
                      </thead>
                      <tbody>
                        {v.entries.map(entry => (
                          <tr key={entry.id} className="border-b border-gray-700/50">
                            <td className="px-4 py-2 text-white">
                              {entry.kol_name}
                              {entry.moin_name && <span className="text-gray-400"> / {entry.moin_name}</span>}
                              {entry.tafzili_name && <span className="text-gray-500"> / {entry.tafzili_name}</span>}
                            </td>
                            <td className="px-4 py-2 text-gray-300">{entry.description || '—'}</td>
                            <td className="px-4 py-2 text-left text-emerald-400 font-bold">
                              {entry.debit ? formatIRR(entry.debit) : '—'}
                            </td>
                            <td className="px-4 py-2 text-left text-blue-400 font-bold">
                              {entry.credit ? formatIRR(entry.credit) : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    {v.status === 'draft' && (
                      <button onClick={() => handleConfirm(v.id)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-500/20 transition">
                        <Check className="w-3.5 h-3.5" /> تأیید سند
                      </button>
                    )}
                    <button onClick={() => handleDelete(v.id)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/20 transition mr-auto">
                      <Trash2 className="w-3.5 h-3.5" /> حذف
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6" dir="rtl">
            <h2 className="text-xl font-bold text-white mb-6">سند حسابداری جدید</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">سال مالی</label>
                  <select value={selectedFY} onChange={e => setSelectedFY(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500">
                    {fiscalYears.map(fy => (
                      <option key={fy.id} value={fy.id}>
                        سال مالی {fy.name}{fy.is_closed ? ' (بسته)' : ' (باز)'}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">تاریخ</label>
                  <input type="text" value={form.date_jalali} onChange={e => setForm(f => ({ ...f, date_jalali: e.target.value }))}
                    placeholder="۱۴۰۴/۰۴/۲۵"
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">شرح</label>
                  <input type="text" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
              </div>

              {/* Entry Lines */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">سطرهای سند</label>
                {form.entries.map((entry, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 mb-2">
                    <select value={entry.kol} onChange={e => {
                      const entries = [...form.entries]; entries[idx].kol = e.target.value; setForm(f => ({ ...f, entries }))
                    }}
                      className="col-span-3 bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-white text-xs focus:outline-none focus:border-emerald-500">
                      <option value="">حساب کل...</option>
                      {kolAccounts.map(k => <option key={k.id} value={k.id}>{k.code} - {k.name}</option>)}
                    </select>
                    <input placeholder="شرح" value={entry.description} onChange={e => {
                      const entries = [...form.entries]; entries[idx].description = e.target.value; setForm(f => ({ ...f, entries }))
                    }}
                      className="col-span-4 bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-white text-xs focus:outline-none focus:border-emerald-500" />
                    <input type="number" placeholder="بدهکار" value={entry.debit} onChange={e => {
                      const entries = [...form.entries]; entries[idx].debit = e.target.value; setForm(f => ({ ...f, entries }))
                    }}
                      className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-white text-xs focus:outline-none focus:border-emerald-500" />
                    <input type="number" placeholder="بستانکار" value={entry.credit} onChange={e => {
                      const entries = [...form.entries]; entries[idx].credit = e.target.value; setForm(f => ({ ...f, entries }))
                    }}
                      className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-white text-xs focus:outline-none focus:border-emerald-500" />
                    <button onClick={() => {
                      setForm(f => ({ ...f, entries: f.entries.filter((_, i) => i !== idx) }))
                    }} className="col-span-1 text-red-400 hover:text-red-300 text-sm flex items-center justify-center">✕</button>
                  </div>
                ))}
                <button onClick={() => setForm(f => ({
                  ...f, entries: [...f.entries, { kol: '', moin: '', tafzili: '', description: '', debit: '', credit: '' }],
                }))} className="text-sm text-emerald-400 hover:text-emerald-300">+ افزودن سطر</button>
              </div>

              {/* Totals */}
              <div className="bg-gray-800/50 rounded-xl p-4 flex justify-between text-sm">
                <span>
                  بدهکار: <span className="text-emerald-400 font-bold">
                    {formatIRR(form.entries.reduce((s, e) => s + (Number(e.debit) || 0), 0))}
                  </span>
                </span>
                <span>
                  بستانکار: <span className="text-blue-400 font-bold">
                    {formatIRR(form.entries.reduce((s, e) => s + (Number(e.credit) || 0), 0))}
                  </span>
                </span>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button onClick={handleCreate} className="flex-1 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition">
                  ایجاد سند
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
