'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { scanApi } from '@/lib/api'
import { Shield, Loader2, AlertCircle, Info } from 'lucide-react'
import { Navbar } from '@/components/layout/Navbar'

const CHAINS = [
  { id: 1, name: 'Ethereum Mainnet' },
  { id: 137, name: 'Polygon' },
  { id: 42161, name: 'Arbitrum One' },
  { id: 8453, name: 'Base' },
]

export default function ScanPage() {
  const router = useRouter()
  const [address, setAddress] = useState('')
  const [chainId, setChainId] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const cleaned = address.trim().toLowerCase()
    if (!cleaned.startsWith('0x') || cleaned.length !== 42) {
      setError('Enter a valid Ethereum address (0x...)')
      return
    }

    setLoading(true)
    try {
      const res = await scanApi.create(cleaned, chainId)
      router.push(`/scan/${res.data.id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to start scan')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="card p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Scan Smart Contract</h1>
              <p className="text-sm text-gray-500">Enter a contract address to begin analysis</p>
            </div>
          </div>

          {error && (
            <div className="mb-5 flex items-start gap-2 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contract Address
              </label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="input font-mono"
                placeholder="0x..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Network / Chain
              </label>
              <select
                value={chainId}
                onChange={(e) => setChainId(Number(e.target.value))}
                className="input"
              >
                {CHAINS.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-700">
              <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>
                Only verified contracts can be scanned. The contract must have its source code
                verified on the block explorer.
              </span>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full text-base py-3">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Starting Scan...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4 mr-2" />
                  Start Security Scan
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-gray-100">
            <p className="text-xs text-gray-500 font-medium mb-3">Analysis includes:</p>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
              {[
                '🔍 Slither Static Analysis',
                '🧠 Heuristic Engine',
                '🤖 CodeBERT ML Scoring',
                '📊 Risk Score Calculation',
                '📄 JSON, MD & PDF Reports',
                '🚦 GO / REVIEW / NO-GO Decision',
              ].map((item) => (
                <div key={item} className="flex items-center gap-1">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
