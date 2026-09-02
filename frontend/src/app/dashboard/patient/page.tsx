'use client'

import { useState } from 'react'
import { useAuthStore } from '@/stores/auth'
import { usePatientDrugSafety, useRerunPatientDrugSafety } from '@/hooks/use-ai'
import { usePatientReminders, useCreateReminder, useDeleteReminder } from '@/hooks/use-reminder'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  AlertTriangle,
  Pill,
  Clock,
  Shield,
  RefreshCw,
  Plus,
  Trash2,
  Info,
  AlertCircle,
  Droplet
} from 'lucide-react'

export default function PatientSafetyDashboard() {
  const { user } = useAuthStore()
  const patientId = user?.id || ''

  // API hooks
  const { data: safetyData, isLoading: safetyLoading } = usePatientDrugSafety(patientId)
  const rerunSafetyMutation = useRerunPatientDrugSafety()
  const { data: reminders, isLoading: remindersLoading } = usePatientReminders()

  const createReminderMutation = useCreateReminder()
  const deleteReminderMutation = useDeleteReminder()

  // Component states
  const [newMedName, setNewMedName] = useState('')
  const [hour12, setHour12] = useState('08')
  const [minute12, setMinute12] = useState('00')
  const [ampm, setAmpm] = useState('AM')
  const [recurrence, setRecurrence] = useState('daily')
  const [validationError, setValidationError] = useState<string | null>(null)

  // Convert 12-hour selection to 24-hour HH:MM format for API
  const get24HourTime = (h12: string, m12: string, period: string) => {
    let hour = parseInt(h12, 10) || 8
    if (period === 'PM' && hour < 12) hour += 12
    if (period === 'AM' && hour === 12) hour = 0
    const hh = String(hour).padStart(2, '0')
    const mm = String(m12).padStart(2, '0')
    return `${hh}:${mm}`
  }

  // Format 24-hour HH:MM string to 12-hour display (e.g. "8:00 PM")
  const format12HourDisplay = (timeStr: string) => {
    if (!timeStr) return ''
    const parts = timeStr.split(':')
    if (parts.length < 2) return timeStr
    let hour = parseInt(parts[0], 10)
    const minute = parts[1].padStart(2, '0')
    if (isNaN(hour)) return timeStr
    const period = hour >= 12 ? 'PM' : 'AM'
    hour = hour % 12 || 12
    return `${hour}:${minute} ${period}`
  }

  // Inline markdown parser for **bold**, *italic*, and `code`
  const parseInlineMarkdown = (content: string): (string | React.JSX.Element)[] => {
    if (!content) return ['']
    const regex = /(\*\*.*?\*\*|\*.*?\*|_.*?_|`.*?`)/g
    const parts = content.split(regex)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
        return <strong key={i} className="font-bold text-slate-900">{parseInlineMarkdown(part.slice(2, -2))}</strong>
      }
      if ((part.startsWith('*') && part.endsWith('*') && part.length >= 2) || (part.startsWith('_') && part.endsWith('_') && part.length >= 2)) {
        return <em key={i} className="italic text-slate-700">{parseInlineMarkdown(part.slice(1, -1))}</em>
      }
      if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
        return <code key={i} className="px-1.5 py-0.5 rounded bg-slate-100 text-teal-800 font-mono text-[11px] border border-slate-200/60">{part.slice(1, -1)}</code>
      }
      return part
    })
  }

  // Render multiline markdown text with bullet points, bolding, and line breaks
  const renderFormattedMarkdown = (text: string) => {
    if (!text) return null
    
    // Split text into lines or bullet points
    const rawLines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
    
    return (
      <div className="space-y-2">
        {rawLines.map((line, idx) => {
          // Check if line is a bullet item
          const isBullet = /^[*\-•]\s+/.test(line)
          const cleanLine = line.replace(/^[*\-•]\s+/, '')
          
          if (isBullet) {
            return (
              <div key={idx} className="flex items-start gap-2 text-xs text-slate-800 font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-teal-600 shrink-0 mt-1.5" />
                <div className="flex-1 leading-relaxed">
                  {parseInlineMarkdown(cleanLine)}
                </div>
              </div>
            )
          }

          return (
            <p key={idx} className="text-xs text-slate-800 leading-relaxed font-medium">
              {parseInlineMarkdown(line)}
            </p>
          )
        })}
      </div>
    )
  }

  const handleAddMedicationReminder = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMedName.trim()) return

    setValidationError(null)
    const final24HrTime = get24HourTime(hour12, minute12, ampm)
    try {
      await createReminderMutation.mutateAsync({
        patient_id: patientId,
        reminder_type: 'medication',
        title: `Take ${newMedName.trim()}`,
        description: `Scheduled dosage of ${newMedName.trim()}`,
        scheduled_time: final24HrTime,
        recurrence: recurrence,
        status: 'active'
      })
      setNewMedName('')
    } catch (err: any) {
      setValidationError(err.message || 'Failed to schedule medication reminder.')
    }
  }

  const getSafetyStatusBadge = (sev: string) => {
    const s = sev?.toUpperCase()
    if (s === 'CRITICAL' || s === 'HIGH') {
      return (
        <Badge className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold px-3.5 py-1.5 flex items-center gap-1.5 rounded-full animate-pulse shadow-sm text-xs">
          <AlertTriangle className="h-4 w-4" /> HAZARD ALERT
        </Badge>
      )
    }
    if (s === 'MEDIUM') {
      return (
        <Badge className="bg-amber-500 hover:bg-amber-600 text-white font-bold px-3.5 py-1.5 flex items-center gap-1.5 rounded-full shadow-sm text-xs">
          <AlertCircle className="h-4 w-4" /> WARNING
        </Badge>
      )
    }
    return (
      <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-3.5 py-1.5 flex items-center gap-1.5 rounded-full shadow-sm text-xs">
        <Shield className="h-4 w-4" /> SAFE
      </Badge>
    )
  }

  const parseExplanation = (text: string) => {
    if (!text) return { warningFlags: [], advice: 'No explanation details.' }
    
    const lines = text.split('\n')
    const warningFlags: string[] = []
    const adviceLines: string[] = []

    lines.forEach(l => {
      const clean = l.trim()
      if (!clean) return
      const lower = clean.toLowerCase()
      if (lower.includes('alcohol') || lower.includes('grapefruit') || lower.includes('tobacco') || lower.includes('dietary')) {
        warningFlags.push(clean.replace(/^[*\-\s•]+/, ''))
      } else {
        adviceLines.push(clean.replace(/^[*\-\s•]+/, ''))
      }
    })

    return {
      warningFlags: warningFlags.slice(0, 3),
      advice: adviceLines.join(' ')
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-4 md:p-6 min-h-screen bg-slate-50/50">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
            <Pill className="h-8 w-8 text-teal-600 animate-pulse" />
            Medication Safety & Reminders
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Schedule medication doses and monitor AI-driven drug safety diagnostics.
          </p>
        </div>
        <Button
          onClick={() => rerunSafetyMutation.mutate(patientId)}
          disabled={rerunSafetyMutation.isPending || safetyLoading}
          variant="outline"
          className="border-teal-200 bg-teal-50/50 hover:bg-teal-100/80 text-teal-800 flex items-center gap-2 self-start md:self-auto font-bold text-xs shadow-2xs transition-all"
        >
          <RefreshCw className={rerunSafetyMutation.isPending ? "h-4 w-4 animate-spin text-teal-600" : "h-4 w-4 text-teal-600"} />
          {rerunSafetyMutation.isPending ? "Running Drug Safety Check..." : "Rerun Drug Safety Check"}
        </Button>
      </div>

      {/* Main Full-Width Section: Schedule Reminder Form & Active Reminders List */}
      <Card className="border border-slate-200 shadow-md bg-white rounded-xl overflow-hidden">
        <CardHeader className="border-b border-slate-100 bg-slate-50/70 p-6">
          <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Plus className="h-5 w-5 text-teal-600" />
            Add & Manage Reminders
          </CardTitle>
        </CardHeader>
        
        <CardContent className="p-6 space-y-6">
          {/* Top Form: Schedule New Reminder */}
          <form onSubmit={handleAddMedicationReminder} className="bg-slate-50/60 p-5 rounded-xl border border-slate-200/80 space-y-4">
            <span className="text-xs font-extrabold text-slate-700 uppercase tracking-wider block">
              Schedule New Medication Reminder
            </span>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Medicine Name */}
              <div className="space-y-1.5 md:col-span-1">
                <label className="text-[11px] font-bold text-slate-600 uppercase">Medication Name</label>
                <Input
                  placeholder="e.g. Aspirin, Ibuprofen, Vitamin D"
                  value={newMedName}
                  onChange={e => setNewMedName(e.target.value)}
                  className="text-xs bg-white border-slate-300 focus:ring-teal-500"
                />
              </div>

              {/* Schedule Time Selectors */}
              <div className="space-y-1.5 md:col-span-1">
                <label className="text-[11px] font-bold text-slate-600 uppercase">Schedule Time</label>
                <div className="flex flex-wrap items-center gap-1.5 min-w-0">
                  <select
                    value={hour12}
                    onChange={e => setHour12(e.target.value)}
                    className="flex-1 min-w-[55px] text-xs border border-slate-300 rounded-lg px-2 py-2 bg-white font-semibold text-slate-700 focus:ring-1 focus:ring-teal-500 shadow-2xs"
                  >
                    {Array.from({ length: 12 }, (_, i) => {
                      const val = String(i + 1).padStart(2, '0')
                      return <option key={val} value={val}>{val}</option>
                    })}
                  </select>
                  <select
                    value={minute12}
                    onChange={e => setMinute12(e.target.value)}
                    className="flex-1 min-w-[55px] text-xs border border-slate-300 rounded-lg px-2 py-2 bg-white font-semibold text-slate-700 focus:ring-1 focus:ring-teal-500 shadow-2xs"
                  >
                    {Array.from({ length: 12 }, (_, i) => {
                      const val = String(i * 5).padStart(2, '0')
                      return <option key={val} value={val}>{val}</option>
                    })}
                  </select>
                  <select
                    value={ampm}
                    onChange={e => setAmpm(e.target.value)}
                    className="flex-1 min-w-[55px] text-xs border border-teal-200 rounded-lg px-2 py-2 bg-teal-50 font-extrabold text-teal-800 focus:ring-1 focus:ring-teal-500 shadow-2xs"
                  >
                    <option value="AM">AM</option>
                    <option value="PM">PM</option>
                  </select>
                </div>
              </div>

              {/* Recurrence & Submit */}
              <div className="space-y-1.5 md:col-span-1 flex flex-col justify-between">
                <label className="text-[11px] font-bold text-slate-600 uppercase">Recurrence</label>
                <div className="flex items-center gap-2">
                  <select
                    value={recurrence}
                    onChange={e => setRecurrence(e.target.value)}
                    className="flex-1 text-xs border border-slate-300 rounded-lg p-2 bg-white font-medium"
                  >
                    <option value="once">Once</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                  </select>
                  <Button
                    type="submit"
                    disabled={createReminderMutation.isPending || !newMedName.trim()}
                    className="bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs flex items-center gap-1.5 px-4 py-2 rounded-lg shadow-sm"
                  >
                    {createReminderMutation.isPending ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    Add Reminder
                  </Button>
                </div>
              </div>
            </div>

            {validationError && (
              <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 text-xs font-semibold flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
                <div>{parseInlineMarkdown(validationError)}</div>
              </div>
            )}
          </form>

          {/* Bottom Section: Active Scheduled Reminders (Scrollable List) */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                <Clock className="h-4 w-4 text-teal-600" />
                Active Scheduled Reminders
              </span>
              <span className="text-xs font-semibold text-slate-400">
                {reminders ? `${reminders.length} active` : '0 active'}
              </span>
            </div>

            {remindersLoading ? (
              <div className="flex flex-col items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-teal-600 mb-2" />
                <span className="text-xs text-slate-400 font-medium">Loading reminders...</span>
              </div>
            ) : reminders && reminders.length > 0 ? (
              <div className="max-h-[380px] overflow-y-auto pr-1.5 space-y-2.5">
                {reminders.map((rem: any) => (
                  <div
                    key={rem.id}
                    className="border border-slate-200 rounded-xl p-3.5 bg-white flex items-center justify-between gap-4 hover:border-teal-200 hover:shadow-2xs transition-all"
                  >
                    <div className="space-y-1 min-w-0 flex-1">
                      <span className="text-sm font-bold text-slate-900 truncate block">
                        {rem.title}
                      </span>
                      <div className="flex items-center gap-2.5 text-xs text-slate-500 font-semibold">
                        <span className="bg-teal-50 text-teal-800 px-2 py-0.5 rounded-md font-bold uppercase text-[10px] border border-teal-100">
                          {rem.reminder_type}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1 font-mono text-slate-700">
                          <Clock className="h-3.5 w-3.5 text-teal-600" />
                          {format12HourDisplay(rem.scheduled_time)}
                        </span>
                        <span>•</span>
                        <span className="capitalize text-slate-500">{rem.recurrence}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-extrabold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 capitalize">
                        {rem.status}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteReminderMutation.mutate(rem.id)}
                        className="p-1.5 h-auto text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        title="Delete reminder"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 border border-dashed border-slate-200 rounded-xl text-center text-slate-400 space-y-1">
                <Pill className="h-8 w-8 mx-auto text-slate-300 mb-2" />
                <p className="text-sm font-semibold text-slate-600">No scheduled reminders</p>
                <p className="text-xs text-slate-400">Use the form above to add your first medication reminder.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Full-Width Section Below: Active Medications Health Overview Card */}
      <Card className="border border-slate-200 shadow-md bg-white overflow-hidden rounded-xl">
        <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-teal-950 p-6 text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] font-black uppercase tracking-wider text-teal-400">Clinical AI Safety Module</span>
            <h2 className="text-xl font-bold">Active Medications Health Overview</h2>
            <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-1">
              <Clock className="h-3.5 w-3.5 text-teal-400" />
              Last Safety Validation: {safetyData ? 'Just now' : 'Fetching...'}
            </div>
          </div>
          <div>
            {safetyLoading || rerunSafetyMutation.isPending ? (
              <RefreshCw className="h-6 w-6 animate-spin text-teal-400" />
            ) : safetyData ? (
              getSafetyStatusBadge(safetyData.severity)
            ) : (
              getSafetyStatusBadge('NONE')
            )}
          </div>
        </div>

        <CardContent className="p-6 space-y-6">
          {safetyLoading || rerunSafetyMutation.isPending ? (
            <div className="flex flex-col items-center justify-center py-10 space-y-2">
              <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-1" />
              <p className="text-sm font-bold text-slate-800">Running AI Drug Safety Agent across active medications...</p>
              <p className="text-xs text-slate-400">Evaluating interaction risks and clinical guidance</p>
            </div>
          ) : safetyData ? (
            <div className="space-y-5">
              {/* Current Medications Badges */}
              <div className="space-y-2">
                <span className="text-xs font-extrabold text-slate-500 uppercase tracking-wider block">
                  Currently Evaluated Active Medications
                </span>
                {safetyData.active_medications?.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {safetyData.active_medications.map((med: string, i: number) => (
                      <Badge key={i} className="bg-teal-50 text-teal-800 hover:bg-teal-100 border border-teal-200 py-1.5 px-3 font-bold uppercase rounded-lg text-xs flex items-center gap-1.5">
                        <Pill className="h-3.5 w-3.5 text-teal-600" /> {med}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No active medications scheduled. Add a reminder above to run safety checks.</p>
                )}
              </div>

              {/* AI Safety Explanation */}
              {safetyData.patient_explanation && (
                <div className="p-4 rounded-xl border border-teal-200/80 bg-teal-50/30 space-y-2">
                  <div className="flex items-center gap-2 font-extrabold text-teal-900 text-xs">
                    <Info className="h-4 w-4 text-teal-600" />
                    AI Patient Safety Guidance
                  </div>
                  <div className="text-slate-700 text-xs leading-relaxed font-medium">
                    {renderFormattedMarkdown(safetyData.patient_explanation)}
                  </div>
                </div>
              )}

              {/* Warning Indicators (e.g. alcohol, food interaction) */}
              {parseExplanation(safetyData.patient_explanation).warningFlags.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                  {parseExplanation(safetyData.patient_explanation).warningFlags.map((flag, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 p-3 rounded-xl border border-amber-200 bg-amber-50/40 text-amber-900 text-xs">
                      <Droplet className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <strong className="block text-[10px] uppercase font-bold text-amber-800">Diet & Lifestyle Warning</strong>
                        <div className="text-[11px] text-slate-700 mt-0.5">{parseInlineMarkdown(flag)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-6 text-slate-400 text-xs">
              No active medication safety findings recorded.
            </div>
          )}

          {/* Safety Disclaimer Banner */}
          <div className="p-4 rounded-xl border border-teal-100 bg-gradient-to-r from-teal-50/40 to-cyan-50/40 flex items-start gap-3 shadow-2xs mt-4">
            <Info className="h-5 w-5 text-teal-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 block">Patient Safety Disclaimer</span>
              <p className="text-[11px] text-slate-600 leading-relaxed font-medium">
                This drug safety check is for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your physician before starting, stopping, or changing any medication.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
