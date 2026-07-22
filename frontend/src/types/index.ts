export type ScanStatus = 'queued' | 'running' | 'completed' | 'failed'
export type Decision = 'GO' | 'REVIEW' | 'NO-GO'
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'informational'
export type Plan = 'free' | 'pro' | 'enterprise'

export interface User {
  id: string
  email: string
  plan: Plan
  is_active: boolean
  created_at: string
}

export interface Vulnerability {
  id: string
  severity: Severity
  detector: string
  description: string
  location: string | null
  source: string | null
}

export interface Provenance {
  contract_address: string
  chain_id: number
  block_number: number | null
  source_hash: string | null
  solc_version: string | null
  slither_version: string | null
  analysis_timestamp: string
}

export interface Scan {
  id: string
  status: ScanStatus
  risk_score: number | null
  decision: Decision | null
  confidence: number | null
  static_score: number | null
  heuristic_score: number | null
  ml_score: number | null
  vulnerabilities: Vulnerability[]
  provenance: Provenance | null
  report_json_url: string | null
  report_md_url: string | null
  report_pdf_url: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface ScanListItem {
  id: string
  address: string
  chain_id: number
  status: ScanStatus
  risk_score: number | null
  decision: Decision | null
  created_at: string
}

export interface Subscription {
  plan: Plan
  status: string
  current_period_end: string | null
}

export interface Usage {
  used: number
  limit: number | null
  unlimited: boolean
}

export const CHAIN_NAMES: Record<number, string> = {
  1: 'Ethereum',
  137: 'Polygon',
  42161: 'Arbitrum',
  8453: 'Base',
}

export const DECISION_CONFIG: Record<Decision, { color: string; bg: string; label: string }> = {
  GO: { color: 'text-green-700', bg: 'bg-green-100', label: '✅ GO' },
  REVIEW: { color: 'text-yellow-700', bg: 'bg-yellow-100', label: '⚠️ REVIEW' },
  'NO-GO': { color: 'text-red-700', bg: 'bg-red-100', label: '🚫 NO-GO' },
}

export const SEVERITY_CONFIG: Record<Severity, { color: string; bg: string }> = {
  critical: { color: 'text-red-700', bg: 'bg-red-100' },
  high: { color: 'text-orange-700', bg: 'bg-orange-100' },
  medium: { color: 'text-yellow-700', bg: 'bg-yellow-100' },
  low: { color: 'text-blue-700', bg: 'bg-blue-100' },
  informational: { color: 'text-gray-700', bg: 'bg-gray-100' },
}
