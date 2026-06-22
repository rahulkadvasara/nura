'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Wallet, IndianRupee, TrendingUp, Clock } from 'lucide-react'

interface EarningsCardProps {
  walletBalance: number
  totalEarnings: number
  pendingBalance: number
}

export function EarningsCard({ walletBalance, totalEarnings, pendingBalance }: EarningsCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value)
  }

  return (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow h-full flex flex-col justify-between">
      <CardHeader className="pb-4 flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-slate-900">
          Earnings Overview
        </CardTitle>
        <div className="p-2 bg-teal-50 rounded-xl">
          <Wallet className="h-5 w-5 text-teal-600" />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <div className="space-y-1">
          <p className="text-sm font-medium text-slate-500">Wallet Balance (Available)</p>
          <div className="flex items-baseline gap-1 text-teal-600">
            <span className="text-3xl font-extrabold tracking-tight">
              {formatCurrency(walletBalance)}
            </span>
          </div>
          <p className="text-xs text-slate-400">Available for payout to your linked bank account</p>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-100">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500">
              <TrendingUp className="h-4 w-4 text-emerald-500" />
              <span className="text-xs font-medium">Total Earnings</span>
            </div>
            <p className="text-lg font-bold text-slate-900">
              {formatCurrency(totalEarnings)}
            </p>
            <p className="text-[10px] text-slate-400">Lifetime earnings</p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500">
              <Clock className="h-4 w-4 text-amber-500" />
              <span className="text-xs font-medium">Pending Clearance</span>
            </div>
            <p className="text-lg font-bold text-slate-900">
              {formatCurrency(pendingBalance)}
            </p>
            <p className="text-[10px] text-slate-400">Held in escrow</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
