import { useState, useEffect } from 'react'
import { getChartOfAccountsTree } from '../../api/finance'
import { useToast } from '../../components/Toast'
import { ChevronDown, ChevronRight, FolderOpen } from 'lucide-react'

interface TafziliItem {
  id: number
  code: string
  name: string
  entity_type: string
}

interface MoinItem {
  id: number
  code: string
  name: string
  tafzilis: TafziliItem[]
}

interface KolItem {
  id: number
  code: string
  name: string
  account_type: string
  normal_balance: string
  moins: MoinItem[]
}

interface GroupItem {
  id: number
  code: string
  name: string
  kols: KolItem[]
}

const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  asset: 'دارایی',
  liability: 'بدهی',
  equity: 'سرمایه',
  revenue: 'درآمد',
  expense: 'هزینه',
}

const BALANCE_LABELS: Record<string, string> = {
  debit: 'بدهکار',
  credit: 'بستانکار',
}

export default function ChartOfAccountsPage() {
  const { toast } = useToast()
  const [tree, setTree] = useState<GroupItem[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set())
  const [expandedKols, setExpandedKols] = useState<Set<number>>(new Set())
  const [expandedMoins, setExpandedMoins] = useState<Set<number>>(new Set())

  useEffect(() => { fetchTree() }, [])

  const fetchTree = async () => {
    try {
      const res = await getChartOfAccountsTree()
      setTree(res.data)
    } catch {
      toast('خطا در دریافت حساب‌ها', 'error')
    } finally {
      setLoading(false)
    }
  }

  const toggleGroup = (id: number) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleKol = (id: number) => {
    setExpandedKols(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleMoin = (id: number) => {
    setExpandedMoins(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
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
          <h1 className="text-2xl font-bold text-white">سرفصل حساب‌ها</h1>
          <p className="text-gray-400 mt-1">گروه ← کل ← معین ← تفصیلی</p>
        </div>
      </div>

      {tree.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <p className="text-lg">هنوز حسابی تعریف نشده</p>
        </div>
      ) : (
        <div className="space-y-2">
          {tree.map(group => (
            <div key={group.id} className="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden">
              {/* Group Header */}
              <button
                onClick={() => toggleGroup(group.id)}
                className="w-full flex items-center gap-3 px-5 py-4 hover:bg-gray-800/50 transition text-right"
              >
                {expandedGroups.has(group.id)
                  ? <ChevronDown className="w-5 h-5 text-gray-400" />
                  : <ChevronRight className="w-5 h-5 text-gray-400" />
                }
                <span className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center text-white text-sm font-bold">
                  {group.code}
                </span>
                <span className="text-lg font-bold text-white">{group.name}</span>
                <span className="text-xs text-gray-500 mr-auto">{group.kols.length} حساب کل</span>
              </button>

              {/* Kol Accounts */}
              {expandedGroups.has(group.id) && (
                <div className="border-t border-gray-800 pr-12">
                  {group.kols.map(kol => (
                    <div key={kol.id}>
                      <button
                        onClick={() => toggleKol(kol.id)}
                        className="w-full flex items-center gap-3 px-5 py-3 hover:bg-gray-800/30 transition text-right"
                      >
                        {expandedKols.has(kol.id)
                          ? <ChevronDown className="w-4 h-4 text-gray-500" />
                          : <ChevronRight className="w-4 h-4 text-gray-500" />
                        }
                        <span className="text-sm font-mono text-emerald-400">{kol.code}</span>
                        <span className="text-white">{kol.name}</span>
                        <span className="text-xs text-gray-500 px-2 py-0.5 bg-gray-800 rounded-full">
                          {ACCOUNT_TYPE_LABELS[kol.account_type] || kol.account_type}
                        </span>
                        <span className="text-xs text-gray-600 px-2 py-0.5 bg-gray-800/50 rounded-full">
                          {BALANCE_LABELS[kol.normal_balance] || kol.normal_balance}
                        </span>
                      </button>

                      {/* Moin Accounts */}
                      {expandedKols.has(kol.id) && (
                        <div className="pr-8">
                          {kol.moins.map(moin => (
                            <div key={moin.id}>
                              <button
                                onClick={() => toggleMoin(moin.id)}
                                className="w-full flex items-center gap-3 px-5 py-2.5 hover:bg-gray-800/20 transition text-right"
                              >
                                {expandedMoins.has(moin.id)
                                  ? <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
                                  : <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
                                }
                                <span className="text-xs font-mono text-cyan-400">{moin.code}</span>
                                <span className="text-gray-300">{moin.name}</span>
                                <span className="text-xs text-gray-600 mr-auto">
                                  {moin.tafzilis.length} تفصیلی
                                </span>
                              </button>

                              {/* Tafzili Accounts */}
                              {expandedMoins.has(moin.id) && moin.tafzilis.length > 0 && (
                                <div className="pr-8 pb-2">
                                  {moin.tafzilis.map(t => (
                                    <div key={t.id} className="flex items-center gap-3 px-5 py-1.5 text-right">
                                      <span className="text-xs font-mono text-purple-400">{t.code}</span>
                                      <span className="text-gray-400 text-sm">{t.name}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
