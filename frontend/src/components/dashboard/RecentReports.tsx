'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Upload } from 'lucide-react'

interface RecentReportsProps {
  count: number
}

export function RecentReports({ count }: RecentReportsProps) {
  return (
    <Card className="border-slate-200 shadow-sm h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-slate-900">
            Recent Reports
          </CardTitle>
          <Link
            href="/dashboard/records"
            className="text-sm font-medium text-teal-600 hover:text-teal-700 transition-colors"
          >
            View all
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {count === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="p-4 rounded-full bg-slate-100 mb-4">
              <FileText className="h-6 w-6 text-slate-400" />
            </div>
            <p className="text-sm font-medium text-slate-700 mb-1">
              No reports yet
            </p>
            <p className="text-xs text-slate-400 mb-5 max-w-[220px]">
              Upload lab results or scans for Nura to analyze.
            </p>
            <Link href="/dashboard/records">
              <Button
                size="sm"
                className="bg-teal-600 hover:bg-teal-700 text-white rounded-lg"
              >
                <Upload className="h-4 w-4 mr-1" />
                Upload Report
              </Button>
            </Link>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-3xl font-bold text-slate-900 mb-1">{count}</p>
            <p className="text-sm text-slate-500">report{count !== 1 ? 's' : ''} uploaded</p>
            <Link href="/dashboard/records" className="mt-4">
              <Button
                variant="outline"
                size="sm"
                className="border-teal-200 text-teal-700 hover:bg-teal-50 rounded-lg"
              >
                View Reports
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
