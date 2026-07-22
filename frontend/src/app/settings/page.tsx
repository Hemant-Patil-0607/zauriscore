'use client'

import { useState } from 'react'
import { useSession } from 'next-auth/react'
import { useQuery } from '@tanstack/react-query'
import { billingApi } from '@/lib/api'
import { Navbar } from '@/components/layout/Navbar'
import { User, Shield, BarChart3, CreditCard } from 'lucide-react'
import Link from 'next/link'

export default function SettingsPage() {
  const { data: session } = useSession()
  const { data: usage } = useQuery({
    queryKey: ['usage'],
    queryFn: () => billingApi.getUsage().then((r) => r.data),
  })
  const { data: sub } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => billingApi.getSubscription().then((r) => r.data),
  })

  const plan = (session?.user as any)?.plan || 'free'

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Account Settings</h1>

        {/* Profile */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="h-5 w-5 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Profile</h2>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Email</p>
              <p className="font-medium text-gray-900 mt-0.5">{session?.user?.email}</p>
            </div>
            <div>
              <p className="text-gray-500">Plan</p>
              <span className="inline-flex mt-0.5 badge bg-blue-100 text-blue-700 capitalize font-semibold">
                {plan}
              </span>
            </div>
          </div>
        </div>

        {/* Usage */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 className="h-5 w-5 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Usage Today</h2>
          </div>
          {usage ? (
            usage.unlimited ? (
              <p className="text-sm text-gray-600">Unlimited scans (Enterprise plan)</p>
            ) : (
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-600">Scans used</span>
                  <span className="font-medium">{usage.used} / {usage.limit}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      usage.used / usage.limit > 0.8 ? 'bg-red-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(100, (usage.used / usage.limit) * 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-2">Resets daily at midnight UTC</p>
              </div>
            )
          ) : (
            <p className="text-sm text-gray-400">Loading...</p>
          )}
        </div>

        {/* Subscription */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <CreditCard className="h-5 w-5 text-blue-600" />
              <h2 className="font-semibold text-gray-900">Subscription</h2>
            </div>
            <Link href="/billing" className="text-sm text-blue-600 hover:text-blue-700">
              Manage →
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Current plan</p>
              <p className="font-medium text-gray-900 capitalize mt-0.5">{sub?.plan || plan}</p>
            </div>
            <div>
              <p className="text-gray-500">Status</p>
              <p className="font-medium text-gray-900 mt-0.5 capitalize">{sub?.status || 'active'}</p>
            </div>
            {sub?.current_period_end && (
              <div>
                <p className="text-gray-500">Next billing date</p>
                <p className="font-medium text-gray-900 mt-0.5">
                  {new Date(sub.current_period_end).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Security */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="h-5 w-5 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Security</h2>
          </div>
          <div className="text-sm text-gray-600 space-y-2">
            <p>✅ JWT-secured session</p>
            <p>✅ Rate limiting active</p>
            <p>✅ All analysis runs in isolated containers</p>
          </div>
        </div>
      </div>
    </div>
  )
}
