'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { billingApi } from '@/lib/api'
import { Navbar } from '@/components/layout/Navbar'
import { Shield, Zap, Building2, Check, Loader2 } from 'lucide-react'

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: '/month',
    icon: Shield,
    color: 'text-gray-600',
    border: 'border-gray-200',
    features: ['5 scans / day', 'JSON & Markdown reports', 'Basic vulnerability detection', 'Community support'],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$49',
    period: '/month',
    icon: Zap,
    color: 'text-blue-600',
    border: 'border-blue-400',
    badge: 'Most Popular',
    features: ['100 scans / day', 'PDF reports', 'ML risk scoring', 'Priority queue', 'Email support'],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: '$299',
    period: '/month',
    icon: Building2,
    color: 'text-purple-600',
    border: 'border-purple-300',
    features: ['Unlimited scans', 'API access', 'CI/CD integration', 'Custom detectors', 'SLA & dedicated support'],
  },
]

export default function BillingPage() {
  const [upgrading, setUpgrading] = useState<string | null>(null)

  const { data: sub } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => billingApi.getSubscription().then((r) => r.data),
  })

  const { data: usage } = useQuery({
    queryKey: ['usage'],
    queryFn: () => billingApi.getUsage().then((r) => r.data),
  })

  const handleUpgrade = async (plan: string) => {
    if (plan === 'free') return
    setUpgrading(plan)
    try {
      const res = await billingApi.createCheckout(plan)
      window.location.href = res.data.checkout_url
    } catch (err: any) {
      alert(err.message || 'Checkout failed')
      setUpgrading(null)
    }
  }

  const currentPlan = sub?.plan || 'free'

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-12 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing & Plans</h1>
          <p className="text-gray-500 mt-1">
            Current plan: <span className="font-semibold capitalize">{currentPlan}</span>
            {usage && !usage.unlimited && (
              <span className="ml-3 text-sm">
                · {usage.used} / {usage.limit} scans used today
              </span>
            )}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => {
            const Icon = plan.icon
            const isCurrent = currentPlan === plan.id
            const isLoading = upgrading === plan.id

            return (
              <div
                key={plan.id}
                className={`card p-6 flex flex-col border-2 ${plan.border} ${isCurrent ? 'ring-2 ring-blue-500' : ''} relative`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="badge bg-blue-600 text-white px-3 py-1 text-xs font-semibold">
                      {plan.badge}
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-2 mb-4">
                  <Icon className={`h-5 w-5 ${plan.color}`} />
                  <h3 className="font-bold text-gray-900">{plan.name}</h3>
                  {isCurrent && <span className="badge bg-blue-100 text-blue-700 ml-auto">Current</span>}
                </div>

                <div className="mb-5">
                  <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
                  <span className="text-gray-500 text-sm">{plan.period}</span>
                </div>

                <ul className="space-y-2 flex-1 mb-6">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                      <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>

                {isCurrent ? (
                  <button disabled className="btn-secondary w-full opacity-60 cursor-default">
                    Current Plan
                  </button>
                ) : plan.id === 'free' ? (
                  <button disabled className="btn-secondary w-full opacity-60 cursor-default">
                    Downgrade
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={!!upgrading}
                    className="btn-primary w-full"
                  >
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Upgrade to {plan.name}
                  </button>
                )}
              </div>
            )
          })}
        </div>

        {sub?.current_period_end && (
          <p className="text-sm text-gray-500 text-center">
            Current period ends: {new Date(sub.current_period_end).toLocaleDateString()}
          </p>
        )}
      </div>
    </div>
  )
}
