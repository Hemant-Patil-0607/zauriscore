'use client'

import { useQuery } from '@tanstack/react-query'
import { scanApi, billingApi } from '@/lib/api'
import { ScanListItem, CHAIN_NAMES, DECISION_CONFIG } from '@/types'
import Link from 'next/link'
import { Shield, Search, TrendingUp, AlertTriangle, Plus, Loader2, ExternalLink } from 'lucide-react'
import { useSession } from 'next-auth/react'
import { formatDistanceToNow } from 'date-fns'

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? 'bg-red-500' : score >= 40 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-sm font-medium w-10 text-right">{score}</span>
    </div>
  )
}

export default function DashboardPage() {
  const { data: session } = useSession()

  const { data: scans, isLoading: scansLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: () => scanApi.list(20, 0).then((r) => r.data as ScanListItem[]),
  })

  const { data: usage } = useQuery({
    queryKey: ['usage'],
    queryFn: () => billingApi.getUsage().then((r) => r.data),
  })

  const completedScans = scans?.filter((s) => s.status === 'completed') || []
  const avgScore =
    completedScans.length > 0
      ? Math.round(completedScans.reduce((sum, s) => sum + (s.risk_score || 0), 0) / completedScans.length)
      : 0
  const highRisk = completedScans.filter((s) => s.decision === 'NO-GO').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">
            Welcome back, {session?.user?.email}
          </p>
        </div>
        <Link href="/scan" className="btn-primary gap-2">
          <Plus className="h-4 w-4" />
          New Scan
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-9 w-9 rounded-lg bg-blue-100 flex items-center justify-center">
              <Search className="h-5 w-5 text-blue-600" />
            </div>
            <span className="text-sm text-gray-500">Total Scans</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{scans?.length || 0}</p>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-9 w-9 rounded-lg bg-green-100 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
            <span className="text-sm text-gray-500">Avg Risk Score</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{avgScore}</p>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-9 w-9 rounded-lg bg-red-100 flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
            <span className="text-sm text-gray-500">High Risk</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{highRisk}</p>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-9 w-9 rounded-lg bg-purple-100 flex items-center justify-center">
              <Shield className="h-5 w-5 text-purple-600" />
            </div>
            <span className="text-sm text-gray-500">Scans Today</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {usage?.unlimited ? '∞' : `${usage?.used || 0}/${usage?.limit || 5}`}
          </p>
        </div>
      </div>

      {/* Scan history */}
      <div className="card">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Recent Scans</h2>
          <Link href="/scan" className="text-sm text-blue-600 hover:text-blue-700">
            New scan →
          </Link>
        </div>

        {scansLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          </div>
        ) : !scans?.length ? (
          <div className="text-center py-12 text-gray-500">
            <Shield className="h-10 w-10 mx-auto mb-3 text-gray-300" />
            <p>No scans yet. Start by scanning a contract.</p>
            <Link href="/scan" className="btn-primary mt-4 inline-flex">
              Scan a Contract
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {scans.map((scan) => (
              <Link
                key={scan.id}
                href={`/scan/${scan.id}`}
                className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <code className="text-sm font-mono text-gray-900 truncate">
                      {scan.address}
                    </code>
                    <span className="badge bg-gray-100 text-gray-600 text-xs">
                      {CHAIN_NAMES[scan.chain_id] || `Chain ${scan.chain_id}`}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">
                    {formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })}
                  </p>
                </div>

                <div className="w-32 hidden sm:block">
                  {scan.risk_score != null ? (
                    <ScoreBar score={scan.risk_score} />
                  ) : (
                    <span className="text-xs text-gray-400">—</span>
                  )}
                </div>

                {scan.decision ? (
                  <span className={`badge ${DECISION_CONFIG[scan.decision].bg} ${DECISION_CONFIG[scan.decision].color} font-semibold`}>
                    {DECISION_CONFIG[scan.decision].label}
                  </span>
                ) : (
                  <span className={`badge ${scan.status === 'failed' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>
                    {scan.status}
                  </span>
                )}

                <ExternalLink className="h-4 w-4 text-gray-300 flex-shrink-0" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
