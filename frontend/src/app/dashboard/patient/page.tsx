'use client'

import { useState } from 'react'
import { useAuthStore } from '@/stores/auth'
import { usePatientDrugSafety, useDrugValidationHistory } from '@/hooks/use-ai'
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
  CheckCircle,
  RefreshCw,
  Plus,
  Trash2,
  Calendar,
  Info,
  ChevronDown,
  ChevronUp,
  Activity,
  AlertCircle,
  Heart,
  Droplet
} from 'lucide-react'

export default function PatientSafetyDashboard() {
  const { user } = useAuthStore()
  const patientId = user?.id || ''

  // API hooks
  const { data: safetyData, isLoading: safetyLoading, isError: safetyError, refetch: refetchSafety } = usePatientDrugSafety(patientId)
  const { data: historyData, isLoading: historyLoading } = useDrugValidationHistory(patientId)
  const { data: reminders, isLoading: remindersLoading } = usePatientReminders()

  const createReminderMutation = useCreateReminder()
  const deleteReminderMutation = useDeleteReminder()

  // Component states
  const [newMedName, setNewMedName] = useState('')
  const [scheduledTime, setScheduledTime] = useState('08:00')
  const [recurrence, setRecurrence] = useState('daily')
  const [validationError, setValidationError] = useState<string | null>(null)
  const [expandedInteractions, setExpandedInteractions] = useState<Record<number, boolean>>({})

  const toggleExpand = (index: number) => {
    setExpandedInteractions(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const handleAddMedicationReminder = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMedName.trim()) return

    setValidationError(null)
    try {
      await createReminderMutation.mutateAsync({
        patient_id: patientId,
        reminder_type: 'medication',
        title: `Take ${newMedName.trim()}`,
        description: `Scheduled dosage of ${newMedName.trim()}`,
        scheduled_time: scheduledTime,
        recurrence: recurrence,
        status: 'active'
      })
      setNewMedName('')
    } catch (err: any) {
      setValidationError(err.message || 'Failed to schedule medication reminder due to safety limits.')
    }
  }

  const getSeverityColor = (sev: string) => {
    switch (sev?.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return 'bg-rose-50 text-rose-700 border-rose-200'
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200'
      case 'LOW':
        return 'bg-blue-50 text-blue-700 border-blue-200'
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200'
    }
  }

  const getSafetyStatusBadge = (sev: string) => {
    const s = sev?.toUpperCase()
    if (s === 'CRITICAL' || s === 'HIGH') {
      return (
        <Badge className="bg-red-500 hover:bg-red-600 text-white font-extrabold px-3 py-1 flex items-center gap-1 rounded-full animate-pulse shadow-sm">
          <AlertTriangle className="h-4 w-4" /> DANGER
        </Badge>
      )
    }
    if (s === 'MEDIUM') {
      return (
        <Badge className="bg-amber-500 hover:bg-amber-600 text-white font-bold px-3 py-1 flex items-center gap-1 rounded-full shadow-sm">
          <AlertCircle className="h-4 w-4" /> WARNING
        </Badge>
      )
    }
    return (
      <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-3 py-1 flex items-center gap-1 rounded-full shadow-sm">
        <Shield className="h-4 w-4" /> SAFE
      </Badge>
    )
  }

  const parseExplanation = (text: string) => {
    if (!text) return { warningFlags: [], advice: 'No explanation details.' }
    
    // Simple parser for bullet sections
    const lines = text.split('\n')
    const warningFlags: string[] = []
    const adviceLines: string[] = []

    lines.forEach(l => {
      const clean = l.trim()
      if (!clean) return
      if (clean.toLowerCase().includes('alcohol') || clean.toLowerCase().includes('avoid') || clean.toLowerCase().includes('warning')) {
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
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 min-h-screen bg-slate-50/50">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2">
            <Pill className="h-8 w-8 text-teal-600 animate-pulse" />
            Medication Safety & Reminders
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time drug interaction checks and clinical safety notifications for your medications list.
          </p>
        </div>
        <Button
          onClick={() => {
            refetchSafety()
          }}
          variant="outline"
          className="border-slate-300 hover:bg-slate-100 flex items-center gap-2 self-start md:self-auto font-semibold text-xs"
        >
          <RefreshCw className="h-4 w-4" /> Refetch Safety Summary
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left/Middle Column: Medication Safety & Details */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Medication Safety Card */}
          <Card className="border border-slate-200 shadow-md bg-white overflow-hidden rounded-xl">
            <div className="bg-gradient-to-r from-slate-900 to-teal-950 p-6 text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-black uppercase tracking-wider text-teal-400">Clinical Safety Module</span>
                <h2 className="text-xl font-bold">Active Medications Health Overview</h2>
                <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-1">
                  <Clock className="h-3.5 w-3.5" />
                  Last Safety Validation: {safetyData ? 'Just now' : 'Fetching...'}
                </div>
              </div>
              <div>
                {safetyLoading ? (
                  <RefreshCw className="h-6 w-6 animate-spin text-teal-400" />
                ) : safetyData ? (
                  getSafetyStatusBadge(safetyData.severity)
                ) : (
                  getSafetyStatusBadge('NONE')
                )}
              </div>
            </div>

            <CardContent className="p-6 space-y-6">
              {safetyLoading ? (
                <div className="flex flex-col items-center justify-center py-10 space-y-2">
                  <RefreshCw className="h-8 w-8 animate-spin text-teal-600" />
                  <p className="text-sm font-semibold text-slate-600">Evaluating active medications interactions...</p>
                </div>
              ) : safetyData ? (
                <div className="space-y-5">
                  {/* Current Medications Badges */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Currently Evaluated Medications</span>
                    {safetyData.active_medications?.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {safetyData.active_medications.map((med: string, i: number) => (
                          <Badge key={i} className="bg-teal-50 text-teal-700 hover:bg-teal-100 border border-teal-200 py-1.5 font-bold uppercase rounded-lg text-xs">
                            <Pill className="h-3 w-3 mr-1" /> {med}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No medications scheduled. Add a reminder to run evaluations.</p>
                    )}
                  </div>

                  {/* AI Safety Explanation */}
                  {safetyData.patient_explanation && (
                    <div className="p-4 rounded-xl border border-teal-100 bg-teal-50/20 space-y-2">
                      <div className="flex items-center gap-1.5 font-bold text-teal-900 text-xs">
                        <Info className="h-4 w-4 text-teal-600" />
                        AI Patient Safety Guidance
                      </div>
                      <p className="text-slate-700 text-xs leading-relaxed font-medium">
                        {safetyData.patient_explanation}
                      </p>
                    </div>
                  )}

                  {/* Warning Indicators (e.g. alcohol, food interaction) */}
                  {parseExplanation(safetyData.patient_explanation).warningFlags.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                      {parseExplanation(safetyData.patient_explanation).warningFlags.map((flag, idx) => (
                        <div key={idx} className="flex items-start gap-2.5 p-3 rounded-lg border border-amber-200 bg-amber-50/30 text-amber-900 text-xs">
                          <Droplet className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                          <div>
                            <strong className="block text-[10px] uppercase font-bold text-amber-800">Diet & Lifestyle Warning</strong>
                            <p className="text-[11px] text-slate-700 mt-0.5">{flag}</p>
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
            </CardContent>
          </Card>

          {/* Medication Details Panel (Interactions Breakdown) */}
          <Card className="border border-slate-200 shadow-md bg-white rounded-xl">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Activity className="h-4 w-4 text-teal-600" />
                Interactions Breakdown Log
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              {safetyData?.interactions?.length > 0 ? (
                <div className="space-y-4">
                  {safetyData.interactions.map((inter: any, idx: number) => {
                    const isExpanded = !!expandedInteractions[idx]
                    return (
                      <div
                        key={idx}
                        className={`border rounded-xl p-4 transition-all ${
                          inter.severity?.toUpperCase() === 'HIGH' || inter.severity?.toUpperCase() === 'CRITICAL'
                            ? 'border-rose-200 bg-rose-50/10'
                            : 'border-slate-200 bg-white'
                        }`}
                      >
                        <div
                          className="flex items-center justify-between gap-4 cursor-pointer"
                          onClick={() => toggleExpand(idx)}
                        >
                          <div className="space-y-1">
                            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                              <AlertTriangle className={`h-4 w-4 ${
                                inter.severity?.toUpperCase() === 'HIGH' || inter.severity?.toUpperCase() === 'CRITICAL' ? 'text-red-500' : 'text-amber-500'
                              }`} />
                              {inter.drug_a} ↔ {inter.drug_b}
                            </span>
                            <span className="text-[10px] text-slate-500 block">Deterministic Medical Recommendation mapping</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className={`uppercase text-[9px] font-bold py-0.5 border ${getSeverityColor(inter.severity)}`}>
                              {inter.severity}
                            </Badge>
                            {isExpanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="mt-4 pt-3 border-t border-dashed border-slate-200 text-xs text-slate-700 space-y-3">
                            <div>
                              <strong className="block text-[10px] uppercase font-bold text-slate-500 mb-1">Severity Description</strong>
                              <p className="leading-relaxed text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                                {inter.description || 'Consult physician regarding concurrent usage of these active compounds.'}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-10 text-center text-slate-400">
                  <CheckCircle className="h-10 w-10 text-emerald-500 mb-2" />
                  <p className="text-sm font-semibold text-slate-700">No drug safety hazards detected</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Your current medication list has no known contraindications.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Safety Disclaimer */}
          <div className="p-4 rounded-xl border border-teal-100 bg-gradient-to-r from-teal-50/30 to-cyan-50/30 flex items-start gap-3 shadow-2xs">
            <Info className="h-5 w-5 text-teal-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 block">Patient Safety Disclaimer</span>
              <p className="text-[11px] text-slate-600 leading-relaxed font-medium">
                This drug safety check is for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your physician before starting, stopping, or changing any medication.
              </p>
            </div>
          </div>

        </div>

        {/* Right Column: Reminders & Validation History */}
        <div className="space-y-6">
          
          {/* Active Reminders List */}
          <Card className="border border-slate-200 shadow-md bg-white rounded-xl">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Clock className="h-4 w-4 text-teal-600" />
                Active Reminders
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              {remindersLoading ? (
                <div className="flex items-center justify-center py-6">
                  <RefreshCw className="h-6 w-6 animate-spin text-teal-600" />
                </div>
              ) : reminders && reminders.length > 0 ? (
                <div className="space-y-3">
                  {reminders.map((rem: any) => (
                    <div key={rem.id} className="border border-slate-200 rounded-lg p-3 bg-white flex items-center justify-between gap-4 hover:shadow-xs transition-all">
                      <div className="space-y-1 min-w-0">
                        <span className="text-xs font-bold text-slate-900 truncate block">{rem.title}</span>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500 font-semibold">
                          <span className="bg-slate-100 px-1.5 py-0.5 rounded uppercase">{rem.reminder_type}</span>
                          <span>•</span>
                          <span>Time: {rem.scheduled_time}</span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteReminderMutation.mutate(rem.id)}
                        className="p-1 h-auto text-slate-400 hover:text-red-600"
                        title="Delete reminder"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic text-center py-6">No scheduled reminders found.</p>
              )}

              {/* Inline Schedule Reminder Form */}
              <form onSubmit={handleAddMedicationReminder} className="border-t border-slate-100 pt-4 space-y-3">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Schedule New Medication Reminder</span>
                
                <div className="space-y-1.5">
                  <label className="text-[10px] font-semibold text-slate-500 uppercase">Medication Name</label>
                  <Input
                    placeholder="e.g. Ibuprofen, Aspirin"
                    value={newMedName}
                    onChange={e => setNewMedName(e.target.value)}
                    className="text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-semibold text-slate-500 uppercase">Schedule Time</label>
                    <Input
                      type="time"
                      value={scheduledTime}
                      onChange={e => setScheduledTime(e.target.value)}
                      className="text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-semibold text-slate-500 uppercase">Recurrence</label>
                    <select
                      value={recurrence}
                      onChange={e => setRecurrence(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-md p-2 bg-white"
                    >
                      <option value="once">Once</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </select>
                  </div>
                </div>

                {validationError && (
                  <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 text-[10px] font-semibold flex items-start gap-1.5">
                    <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
                    <span>{validationError}</span>
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={createReminderMutation.isPending || !newMedName.trim()}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs flex items-center justify-center gap-1.5 shadow-sm"
                >
                  {createReminderMutation.isPending ? (
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Plus className="h-3.5 w-3.5" />
                  )}
                  Schedule Reminder
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Validation History Log */}
          <Card className="border border-slate-200 shadow-md bg-white rounded-xl">
            <CardHeader className="border-b border-slate-100 bg-slate-50/50">
              <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <HistoryIcon className="h-4 w-4 text-teal-600" />
                Validation Safety History
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              {historyLoading ? (
                <div className="flex items-center justify-center py-6">
                  <RefreshCw className="h-6 w-6 animate-spin text-teal-600" />
                </div>
              ) : historyData && historyData.length > 0 ? (
                <div className="space-y-4 max-h-[360px] overflow-y-auto pr-1">
                  {historyData.map((item: any, i: number) => (
                    <div key={i} className="border-b border-slate-100 pb-3 last:border-b-0 space-y-1.5">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="font-bold text-slate-500 uppercase">Run #{historyData.length - i}</span>
                        <span className="text-slate-400 font-semibold">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {item.incoming_medications?.map((m: string, idx: number) => (
                          <Badge key={idx} className="bg-slate-100 border border-slate-200 hover:bg-slate-100 text-slate-700 text-[8px] py-0">
                            {m}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex justify-between items-center text-[10px] pt-1">
                        <span className="text-slate-500">Decision: <strong className={item.decision === 'BLOCK' ? 'text-red-600' : item.decision === 'WARNING' ? 'text-amber-600' : 'text-emerald-600'}>{item.decision}</strong></span>
                        <Badge className={`text-[8px] py-0 border ${getSeverityColor(item.severity)}`}>
                          {item.severity}
                        </Badge>
                      </div>
                      {item.override_reason && (
                        <p className="text-[9px] bg-amber-50 text-amber-800 p-2.5 rounded-lg border border-amber-100 leading-relaxed font-mono">
                          Override: {item.override_reason}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic text-center py-6">No historical runs recorded.</p>
              )}
            </CardContent>
          </Card>

        </div>

      </div>
    </div>
  )
}

function HistoryIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M12 7v5l4 2" />
    </svg>
  )
}
