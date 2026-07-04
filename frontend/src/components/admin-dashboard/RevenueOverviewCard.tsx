'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Wallet, Landmark, TrendingUp } from 'lucide-react'

interface RevenueOverviewCardProps {
  totalRevenue: number
  platformEarnings: number
}

export function RevenueOverviewCard({ totalRevenue, platformEarnings }: RevenueOverviewCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value)
  }

  // Doctor share is totalRevenue - platformEarnings
  const doctorPayouts = totalRevenue - platformEarnings

  return (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow flex flex-col w-full">
      <CardHeader className="pb-4 flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-slate-900">
          Financial Overview
        </CardTitle>
        <div className="p-2 bg-teal-50 rounded-xl">
          <Landmark className="h-5 w-5 text-teal-600" />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {totalRevenue === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-3">
              <TrendingUp className="h-6 w-6 stroke-1.5" />
            </div>
            <p className="text-sm font-semibold text-slate-700">No financial analytics available yet</p>
            <p className="text-xs text-slate-450 mt-1 max-w-[220px]">
              Revenue tracking will initialize automatically once patient consultations begin.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Platform Gross Volume</p>
              <div className="flex items-baseline gap-1 text-teal-600">
                <span className="text-3xl font-extrabold tracking-tight">
                  {formatCurrency(totalRevenue)}
                </span>
              </div>
              <p className="text-xs text-slate-400">Total payments processed through platform checkout</p>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-100">
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-slate-500">
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                  <span className="text-xs font-medium">Platform Share (15%)</span>
                </div>
                <p className="text-lg font-bold text-slate-900">
                  {formatCurrency(platformEarnings)}
                </p>
                <p className="text-[10px] text-slate-400">Net platform revenue</p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-slate-500">
                  <Wallet className="h-4 w-4 text-indigo-500" />
                  <span className="text-xs font-medium">Doctor Share (85%)</span>
                </div>
                <p className="text-lg font-bold text-slate-900">
                  {formatCurrency(doctorPayouts)}
                </p>
                <p className="text-[10px] text-slate-400">Paid to doctor wallets</p>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
