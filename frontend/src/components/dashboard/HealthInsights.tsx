'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sparkles, ArrowRight } from 'lucide-react'
import { RecentHealthInsight } from '@/types'

interface HealthInsightsProps {
  insights: RecentHealthInsight[]
}

function severityColor(severity: string | null) {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-700 border-red-200'
    case 'medium':
      return 'bg-amber-100 text-amber-700 border-amber-200'
    case 'low':
      return 'bg-emerald-100 text-emerald-700 border-emerald-200'
    default:
      return 'bg-slate-100 text-slate-600 border-slate-200'
  }
}

export function HealthInsights({ insights }: HealthInsightsProps) {
  return (
    <Card className="border-teal-200 shadow-sm h-full overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-teal-600" />
          <CardTitle className="text-base font-semibold text-slate-900">
            AI Health Insights
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {insights.length === 0 ? (
          <div className="rounded-xl bg-teal-50 p-5">
            <p className="text-sm font-semibold text-slate-800 mb-2">
              Nura is ready to personalize your insights.
            </p>
            <p className="text-xs text-slate-500 leading-relaxed mb-4">
              Once you upload reports and add health data, Nura will surface
              trends, flag potential risks, and suggest next steps tailored to
              you.
            </p>
            <Link href="/dashboard/chat">
              <Button
                size="sm"
                variant="outline"
                className="border-teal-300 text-teal-700 hover:bg-teal-100 rounded-lg"
              >
                Chat with Nura
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {insights.map((insight) => (
              <div
                key={insight.id}
                className="flex items-start justify-between gap-3 rounded-lg border border-slate-100 p-3 hover:bg-slate-50/50 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-800 truncate">
                    {insight.title}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {new Date(insight.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </p>
                </div>
                {insight.severity && (
                  <Badge
                    className={`text-[10px] px-2 py-0.5 capitalize ${severityColor(insight.severity)}`}
                  >
                    {insight.severity}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
