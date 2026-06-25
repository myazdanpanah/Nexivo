import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useToast } from '../components/Toast'
import { ArrowRight, Building2, FolderTree, Users, ChevronDown, ChevronRight, User, Crown } from 'lucide-react'

interface OrgMember {
  id: number
  username: string
  first_name: string
  last_name: string
  role: string
  email: string
}

interface OrgTeam {
  id: number
  name: string
  manager: OrgMember | null
  members: OrgMember[]
}

interface OrgDivision {
  id: number
  name: string
  manager: OrgMember | null
  teams: OrgTeam[]
  direct_employees: OrgMember[]
}

interface OrgCompany {
  id: number
  name: string
  divisions: OrgDivision[]
  unassigned: OrgMember[]
}

const ROLE_COLORS: Record<string, string> = {
  ceo: 'bg-amber-100 text-amber-700 border-amber-200',
  admin: 'bg-purple-100 text-purple-700 border-purple-200',
  finance: 'bg-blue-100 text-blue-700 border-blue-200',
  sales: 'bg-emerald-100 text-emerald-700 border-emerald-200',
}

const ROLE_LABELS: Record<string, string> = {
  ceo: 'مدیرعامل',
  admin: 'مدیر سیستم',
  finance: 'مالی',
  sales: 'فروش',
}

function MemberCard({ member, compact = false }: { member: OrgMember; compact?: boolean }) {
  const initials = (member.first_name?.[0] || member.username[0] || '').toUpperCase()
  const fullName = [member.first_name, member.last_name].filter(Boolean).join(' ') || member.username

  if (compact) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-100 rounded-xl hover:shadow-sm transition">
        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-xs font-bold text-gray-600 flex-shrink-0">
          {initials}
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium text-gray-800 truncate">{fullName}</p>
          <p className="text-[10px] text-gray-400">{ROLE_LABELS[member.role] || member.role}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 hover:shadow-lg transition group">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-lg font-bold text-indigo-700 group-hover:bg-indigo-200 transition">
          {initials}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-bold text-gray-900 truncate">{fullName}</p>
          <p className="text-xs text-gray-500">@{member.username}</p>
          <span className={`inline-block mt-1 px-2 py-0.5 rounded-lg text-[10px] font-medium border ${ROLE_COLORS[member.role] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
            {ROLE_LABELS[member.role] || member.role}
          </span>
        </div>
      </div>
      {member.email && (
        <p className="text-[10px] text-gray-400 mt-2 truncate">{member.email}</p>
      )}
    </div>
  )
}

function TeamNode({ team }: { team: OrgTeam }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-gray-200 rounded-2xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition text-right"
      >
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-bold text-gray-800">{team.name}</span>
          <span className="text-[10px] bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full">{team.members.length}</span>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>

      {expanded && (
        <div className="p-3 space-y-2 border-t border-gray-100">
          {team.manager && (
            <div>
              <p className="text-[10px] font-medium text-amber-600 mb-1 flex items-center gap-1">
                <Crown className="w-3 h-3" /> سرپرست تیم
              </p>
              <MemberCard member={team.manager} compact />
            </div>
          )}
          {team.members.length > 0 && (
            <div>
              <p className="text-[10px] font-medium text-gray-400 mb-1">اعضا ({team.members.length})</p>
              <div className="space-y-1">
                {team.members.filter(m => m.id !== team.manager?.id).map(m => (
                  <MemberCard key={m.id} member={m} compact />
                ))}
              </div>
            </div>
          )}
          {team.members.length === 0 && !team.manager && (
            <p className="text-xs text-gray-400 text-center py-2">بدون عضو</p>
          )}
        </div>
      )}
    </div>
  )
}

function DivisionNode({ division }: { division: OrgDivision }) {
  const [expanded, setExpanded] = useState(true)
  const totalMembers = (division.direct_employees?.length || 0) +
    division.teams.reduce((sum, t) => sum + t.members.length, 0)

  return (
    <div className="border border-gray-200 rounded-2xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-4 bg-gradient-to-l from-indigo-50 to-white hover:from-indigo-100 transition text-right"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center">
            <FolderTree className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-base font-bold text-gray-900">{division.name}</span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-gray-400">{totalMembers} نفر</span>
              <span className="text-[10px] text-gray-400">·</span>
              <span className="text-[10px] text-gray-400">{division.teams.length} تیم</span>
            </div>
          </div>
        </div>
        {expanded ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}
      </button>

      {expanded && (
        <div className="p-4 space-y-3 border-t border-gray-100">
          {division.manager && (
            <div className="mb-3">
              <p className="text-[10px] font-medium text-amber-600 mb-1 flex items-center gap-1">
                <Crown className="w-3 h-3" /> مدیر واحد
              </p>
              <MemberCard member={division.manager} />
            </div>
          )}

          {division.direct_employees && division.direct_employees.length > 0 && (
            <div className="mb-3">
              <p className="text-[10px] font-medium text-gray-400 mb-1">کارکنان مستقیم</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {division.direct_employees.filter(m => m.id !== division.manager?.id).map(m => (
                  <MemberCard key={m.id} member={m} compact />
                ))}
              </div>
            </div>
          )}

          {division.teams.length > 0 && (
            <div>
              <p className="text-[10px] font-medium text-gray-400 mb-2">تیم‌ها ({division.teams.length})</p>
              <div className="space-y-2 pl-4 border-r-2 border-indigo-100">
                {division.teams.map(team => (
                  <TeamNode key={team.id} team={team} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function OrgChartPage() {
  const [orgTree, setOrgTree] = useState<OrgCompany[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchOrgTree()
  }, [])

  const fetchOrgTree = async () => {
    try {
      const res = await api.get('/auth/org-tree/')
      setOrgTree(res.data.companies || [])
    } catch {
      toast('خطا در دریافت ساختار سازمانی', 'error')
    } finally {
      setLoading(false)
    }
  }

  const totalStats = orgTree.reduce(
    (acc, company) => {
      acc.companies++
      acc.divisions += company.divisions.length
      acc.teams += company.divisions.reduce((s, d) => s + d.teams.length, 0)
      acc.members += company.divisions.reduce(
        (s, d) => s + (d.direct_employees?.length || 0) + d.teams.reduce((ts, t) => ts + t.members.length, 0),
        0
      )
      acc.members += company.unassigned?.length || 0
      return acc
    },
    { companies: 0, divisions: 0, teams: 0, members: 0 }
  )

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboards" className="p-2 text-gray-400 hover:text-gray-600 transition">
              <ArrowRight className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">نمودار سازمانی</h1>
                <p className="text-xs text-gray-500">ساختار سازمانی شرکت و تیم‌ها</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'شرکت', count: totalStats.companies, icon: Building2, color: 'bg-indigo-100 text-indigo-600' },
            { label: 'واحد', count: totalStats.divisions, icon: FolderTree, color: 'bg-purple-100 text-purple-600' },
            { label: 'تیم', count: totalStats.teams, icon: Users, color: 'bg-blue-100 text-blue-600' },
            { label: 'کارمند', count: totalStats.members, icon: User, color: 'bg-emerald-100 text-emerald-600' },
          ].map((stat) => (
            <div key={stat.label} className="bg-white rounded-2xl border border-gray-200 p-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${stat.color}`}>
                  <stat.icon className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{stat.count}</p>
                  <p className="text-xs text-gray-500">{stat.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-20 text-gray-500">در حال بارگذاری...</div>
        ) : orgTree.length === 0 ? (
          <div className="text-center py-20">
            <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">هنوز ساختار سازمانی تعریف نشده</h3>
            <p className="text-gray-500 mb-6">از بخش مدیریت سازمانی شرکت، واحد و تیم اضافه کنید</p>
            <Link
              to="/admin/org"
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition font-medium inline-block"
            >
              رفتن به مدیریت سازمانی
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {orgTree.map((company) => (
              <div key={company.id} className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-l from-indigo-600 to-indigo-500">
                  <div className="flex items-center gap-3">
                    <Building2 className="w-6 h-6 text-white" />
                    <div>
                      <h2 className="text-lg font-bold text-white">{company.name}</h2>
                      <p className="text-xs text-indigo-200">
                        {company.divisions.length} واحد ·{' '}
                        {company.divisions.reduce((s, d) => s + d.teams.length, 0)} تیم
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 space-y-3">
                  {company.divisions.map((division) => (
                    <DivisionNode key={division.id} division={division} />
                  ))}

                  {company.unassigned && company.unassigned.length > 0 && (
                    <div className="border border-dashed border-gray-300 rounded-2xl p-4">
                      <p className="text-xs font-medium text-gray-400 mb-2">بدون واحد سازمانی ({company.unassigned.length})</p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {company.unassigned.map((m) => (
                          <MemberCard key={m.id} member={m} compact />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
