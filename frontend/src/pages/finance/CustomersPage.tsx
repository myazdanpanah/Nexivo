import { useState, useEffect } from 'react'
import { getCustomers, createCustomer, deleteCustomer } from '../../api/finance'
import { useToast } from '../../components/Toast'
import { Plus, Users, Trash2, Search } from 'lucide-react'

interface CustomerItem {
  id: number
  name: string
  national_id: string
  phone: string
  mobile: string
  balance: number
  credit_limit: number
  is_active: boolean
}

const formatIRR = (n: number) => new Intl.NumberFormat('fa-IR').format(n) + ' ریال'

export default function CustomersPage() {
  const { toast } = useToast()
  const [customers, setCustomers] = useState<CustomerItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    name: '', national_id: '', phone: '', mobile: '', email: '', address: '',
  })

  useEffect(() => { fetchCustomers() }, [])

  const fetchCustomers = async () => {
    try {
      const res = await getCustomers(search || undefined)
      setCustomers(res.data)
    } catch {
      toast('خطا در دریافت مشتریان', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => { fetchCustomers() }

  const handleCreate = async () => {
    if (!form.name) { toast('نام مشتری الزامی است', 'error'); return }
    try {
      await createCustomer(form)
      toast('مشتری ایجاد شد', 'success')
      setShowCreate(false)
      setForm({ name: '', national_id: '', phone: '', mobile: '', email: '', address: '' })
      fetchCustomers()
    } catch {
      toast('خطا در ایجاد مشتری', 'error')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('آیا از حذف مطمئن هستید؟')) return
    try {
      await deleteCustomer(id)
      toast('مشتری حذف شد', 'success')
      fetchCustomers()
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
          <h1 className="text-2xl font-bold text-white">مشتریان</h1>
          <p className="text-gray-400 mt-1">{customers.length} مشتری</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition">
          <Plus className="w-4 h-4" />
          مشتری جدید
        </button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="جستجو بر اساس نام یا کد ملی..."
            className="w-full bg-gray-800 border border-gray-700 rounded-xl pr-10 pl-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
          />
        </div>
        <button onClick={handleSearch} className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm transition">
          جستجو
        </button>
      </div>

      {customers.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <Users className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <p className="text-lg">هنوز مشتری ثبت نشده</p>
        </div>
      ) : (
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="px-5 py-3 text-right text-gray-400 font-medium">نام</th>
                  <th className="px-5 py-3 text-right text-gray-400 font-medium">کد ملی</th>
                  <th className="px-5 py-3 text-right text-gray-400 font-medium">تلفن</th>
                  <th className="px-5 py-3 text-right text-gray-400 font-medium">مانده حساب</th>
                  <th className="px-5 py-3 text-right text-gray-400 font-medium">سقف اعتبار</th>
                  <th className="px-5 py-3 text-center text-gray-400 font-medium">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {customers.map(c => (
                  <tr key={c.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition">
                    <td className="px-5 py-3 text-white font-medium">{c.name}</td>
                    <td className="px-5 py-3 text-gray-300 font-mono">{c.national_id || '—'}</td>
                    <td className="px-5 py-3 text-gray-300">{c.phone || c.mobile || '—'}</td>
                    <td className="px-5 py-3 text-emerald-400 font-bold">{formatIRR(c.balance)}</td>
                    <td className="px-5 py-3 text-gray-300">{c.credit_limit ? formatIRR(c.credit_limit) : '—'}</td>
                    <td className="px-5 py-3 text-center">
                      <button onClick={() => handleDelete(c.id)} className="p-1.5 text-gray-500 hover:text-red-400 transition">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg p-6" dir="rtl">
            <h2 className="text-xl font-bold text-white mb-6">مشتری جدید</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">نام *</label>
                <input type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">کد ملی</label>
                  <input type="text" value={form.national_id} onChange={e => setForm(f => ({ ...f, national_id: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">تلفن</label>
                  <input type="text" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">موبایل</label>
                  <input type="text" value={form.mobile} onChange={e => setForm(f => ({ ...f, mobile: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">ایمیل</label>
                  <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">آدرس</label>
                <input type="text" value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500" />
              </div>
              <div className="flex items-center gap-3 pt-2">
                <button onClick={handleCreate} className="flex-1 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition">
                  ایجاد مشتری
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
