'use client'

import { useQuery } from '@tanstack/react-query'
import { scanApi } from '@/lib/api'
import { Scan, DECISION_CONFIG, SEVERITY_CONFIG, CHAIN_NAMES } from '@/types'
import { Navbar } from '@/components/layout/Navbar'
import {
  Shield, Loader2, AlertTriangle, CheckCircle, XCircle,
  Clock, Download, FileText, FileJson, FileCode
} from 'lucide-react'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'

function StatusBadge({ status }: { status: string }) {
  const config = {
    queued: { icon: Clock, color: 'text-gray-600', bg: 'bg-gray-100', label: 'Queued' },
    running: { icon: Loader2, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Analyzing...' },
    completed: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Completed' },
    failed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-100', label: 'Failed' },
  }[status] || { icon: Clock, color: 'text-gray-600', bg: 'bg-gray-100', label: status }

  const Icon = config.icon

  return (
    <span className={`badge ${config.bg} ${config.color} gap-1`}>
      <Icon className={`h-3 w-3 ${status === 'running' ? 'animate-spin' : ''}`} />
      {config.label}
    </span>
  )
}

function ScoreGauge({ score, decision }: { score: number; decision: string | null }) {
  const color = decision === 'GO' ? '#16a34a' : decision === 'REVIEW' ? '#d97706' : '#dc2626'
  const data = [{ value: score, fill: color }, { value: 100 - score, fill: '#f1f5f9' }]

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-48 w-48">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="100%"
            startAngle={180}
            endAngle={0}
            data={data}
          >
            <RadialBar dataKey="value" cornerRadius={10} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center mt-8">
          <span className="text-4xl font-bold" style={{ color }}>{score}</span>
          <span className="text-sm text-gray-500">/ 100</span>
        </div>
      </div>
      {decision && (
        <span className={`badge ${DECISION_CONFIG[decision as keyof typeof DECISION_CONFIG]?.bg} ${DECISION_CONFIG[decision as keyof typeof DECISION_CONFIG]?.color} text-base font-bold px-4 py-1.5 mt-2`}>
          {DECISION_CONFIG[decision as keyof typeof DECISION_CONFIG]?.label}
        </span>
      )}
    </div>
  )
}

export default function ScanResultPage({ params }: { params: { id: string } }) {
  const { data: scan, isLoading, error } = useQuery({
    queryKey: ['scan', params.id],
    queryFn: () => scanApi.get(params.id).then((r) => r.data as Scan),
    refetchInterval: (query) => {
      const data = query.state.data as Scan | undefined
      if (!data || data.status === 'queued' || data.status === 'running') return 3000
      return false
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      </div>
    )
  }

  if (error || !scan) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-12 text-center text-red-600">
          Failed to load scan.
        </div>
      </div>
    )
  }

  const isProcessing = scan.status === 'queued' || scan.status === 'running'
  const vulnCounts = scan.vulnerabilities.reduce((acc, v) => {
    acc[v.severity] = (acc[v.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="card p-6">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Shield className="h-5 w-5 text-blue-600" />
                <h1 className="text-lg font-bold text-gray-900">Security Analysis Report</h1>
                <StatusBadge status={scan.status} />
              </div>
              <code className="text-sm text-gray-600 font-mono">
                {scan.provenance?.contract_address || '—'}
              </code>
              {scan.provenance?.chain_id && (
                <span className="ml-2 badge bg-gray-100 text-gray-600">
                  {CHAIN_NAMES[scan.provenance.chain_id]}
                </span>
              )}
            </div>
            {scan.status === 'completed' && (
              <div className="flex gap-2">
                {scan.report_json_url && (
                  <a href={scan.report_json_url} target="_blank" rel="noreferrer" className="btn-secondary gap-1 text-sm">
                    <FileJson className="h-4 w-4" /> JSON
                  </a>
                )}
                {scan.report_md_url && (
                  <a href={scan.report_md_url} target="_blank" rel="noreferrer" className="btn-secondary gap-1 text-sm">
                    <FileCode className="h-4 w-4" /> MD
                  </a>
                )}
                {scan.report_pdf_url && (
                  <a href={scan.report_pdf_url} target="_blank" rel="noreferrer" className="btn-primary gap-1 text-sm">
                    <Download className="h-4 w-4" /> PDF
                  </a>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Processing state */}
        {isProcessing && (
          <div className="card p-10 flex flex-col items-center gap-4 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
            <div>
              <p className="font-semibold text-gray-900 text-lg">
                {scan.status === 'queued' ? 'In Queue...' : 'Analyzing Contract...'}
              </p>
              <p className="text-gray-500 text-sm mt-1">
                Running Slither, heuristics, and ML analysis. This takes up to 90 seconds.
              </p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2 text-sm text-gray-500">
              {['Source Retrieval', 'Compilation', 'Slither Analysis', 'Heuristics', 'ML Engine', 'Report Generation'].map(stage => (
                <div key={stage} className="flex items-center gap-1.5">
                  <div className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
                  {stage}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Failed state */}
        {scan.status === 'failed' && (
          <div className="card p-6 border-red-200 bg-red-50">
            <div className="flex items-start gap-3">
              <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
              <div>
                <p className="font-semibold text-red-800">Scan Failed</p>
                <p className="text-sm text-red-700 mt-1">{scan.error_message || 'Unknown error occurred'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {scan.status === 'completed' && scan.risk_score != null && (
          <>
            {/* Score + breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card p-6 flex flex-col items-center justify-center">
                <ScoreGauge score={scan.risk_score} decision={scan.decision} />
                <p className="text-sm text-gray-500 mt-3">Confidence: {scan.confidence}%</p>
              </div>

              <div className="card p-6 space-y-4">
                <h3 className="font-semibold text-gray-900">Score Breakdown</h3>
                {[
                  { label: 'Static Analysis (Slither)', value: scan.static_score || 0, weight: '50%' },
                  { label: 'Heuristic Engine', value: scan.heuristic_score || 0, weight: '30%' },
                  { label: 'ML Engine (CodeBERT)', value: scan.ml_score || 0, weight: '20%' },
                ].map(({ label, value, weight }) => (
                  <div key={label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">{label}</span>
                      <span className="font-medium">{value.toFixed(1)} <span className="text-gray-400 text-xs">({weight})</span></span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${value >= 70 ? 'bg-red-500' : value >= 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </div>
                ))}

                {/* Severity summary */}
                <div className="pt-3 border-t border-gray-100">
                  <p className="text-sm font-medium text-gray-700 mb-2">Vulnerabilities by Severity</p>
                  <div className="flex flex-wrap gap-2">
                    {(['critical', 'high', 'medium', 'low', 'informational'] as const).map(sev => {
                      const count = vulnCounts[sev] || 0
                      if (!count) return null
                      return (
                        <span key={sev} className={`badge ${SEVERITY_CONFIG[sev].bg} ${SEVERITY_CONFIG[sev].color}`}>
                          {sev}: {count}
                        </span>
                      )
                    })}
                    {!scan.vulnerabilities.length && (
                      <span className="text-sm text-green-600">✅ No vulnerabilities found</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Vulnerabilities list */}
            {scan.vulnerabilities.length > 0 && (
              <div className="card">
                <div className="p-5 border-b border-gray-100">
                  <h2 className="font-semibold text-gray-900">
                    Vulnerabilities ({scan.vulnerabilities.length})
                  </h2>
                </div>
                <div className="divide-y divide-gray-50">
                  {scan.vulnerabilities.map((v) => (
                    <div key={v.id} className="p-4">
                      <div className="flex items-start gap-3">
                        <span className={`badge ${SEVERITY_CONFIG[v.severity as keyof typeof SEVERITY_CONFIG]?.bg} ${SEVERITY_CONFIG[v.severity as keyof typeof SEVERITY_CONFIG]?.color} mt-0.5`}>
                          {v.severity}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 text-sm">{v.detector}</p>
                          <p className="text-sm text-gray-600 mt-1">{v.description}</p>
                          {v.location && (
                            <code className="text-xs text-gray-400 mt-1 block">{v.location}</code>
                          )}
                        </div>
                        <span className="badge bg-gray-50 text-gray-500 text-xs">{v.source}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Provenance */}
            {scan.provenance && (
              <div className="card p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Provenance Metadata</h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                  {[
                    { label: 'Solc Version', value: scan.provenance.solc_version },
                    { label: 'Slither Version', value: scan.provenance.slither_version },
                    { label: 'Block Number', value: scan.provenance.block_number },
                    { label: 'Source Hash', value: scan.provenance.source_hash ? `${scan.provenance.source_hash.slice(0, 16)}...` : '—' },
                    { label: 'Analysis Time', value: new Date(scan.provenance.analysis_timestamp).toUTCString() },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <p className="text-gray-500 text-xs">{label}</p>
                      <p className="font-mono text-gray-900 text-xs mt-0.5">{value || '—'}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
