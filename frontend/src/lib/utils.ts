import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getCleanFileName(report: any): string {
  if (!report) return 'Medical Report'

  // 1. If file_metadata or report object has original_filename, use it
  if (report.file_metadata?.original_filename) {
    return report.file_metadata.original_filename
  }
  if (report.original_filename) {
    return report.original_filename
  }

  // 2. Strip URL query string (e.g. ?token=...) and hash fragments
  const rawUrl = report.file_url || report.file_name || ''
  if (!rawUrl) return 'Medical Report'

  const cleanUrl = rawUrl.split('?')[0].split('#')[0]
  const filename = cleanUrl.split('/').pop() || 'Medical Report'

  return filename
}