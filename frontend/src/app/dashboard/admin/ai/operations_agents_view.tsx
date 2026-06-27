'use client'

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { 
  useReminderAgentTest, 
  useAppointmentAgentTest, 
  useOperationsAgentsStatistics 
} from '@/hooks/use-ai'
import { 
  RefreshCw, 
  Bell, 
  Calendar, 
  ShieldAlert, 
  Info,
  CheckCircle2, 
  AlertTriangle,
  Play
} from 'lucide-react'

export function OperationsAgentsView() {
  const [activePlayground, setActivePlayground] = useState<'reminder' | 'appointment'>('reminder')
  
  const [reminderQuery, setReminderQuery] = useState('Create a daily reminder for taking Aspirin 100mg at 08:00')
  const [reminderPatientId, setReminderPatientId] = useState('65f7c32b5e28a425fca68341')
  const [reminderDebug, setReminderDebug] = useState(false)
  
  const [appointmentQuery, setAppointmentQuery] = useState('Find a dermatologist specialized in acne and show available slots.')
  const [appointmentPatientId, setAppointmentPatientId] = useState('65f7c32b5e28a425fca68341')
  const [appointmentDebug, setAppointmentDebug] = useState(false)

  const reminderMutation = useReminderAgentTest()
  const appointmentMutation = useAppointmentAgentTest()
  
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useOperationsAgentsStatistics()

  const handleTestReminder = () => {
    reminderMutation.mutate({
      query: reminderQuery,
      patient_id: reminderPatientId || undefined,
      debug_mode: reminderDebug
    })
  }

  const handleTestAppointment = () => {
    appointmentMutation.mutate({
      query: appointmentQuery,
      patient_id: appointmentPatientId || undefined,
      debug_mode: appointmentDebug
    })
  }

  const getAgentStat = (agentName: string, metric: string, defaultValue: any = 0) => {
    if (!stats || !stats[agentName]) return defaultValue
    return stats[agentName][metric] ?? defaultValue
  }

  return (
    <div className="space-y-6">
      {/* Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[
          { name: 'ReminderAgent', display: 'Reminder Operations Agent', icon: Bell },
          { name: 'AppointmentAgent', display: 'Appointment Operations Agent', icon: Calendar }
        ].map(({ name, display, icon: Icon }) => {
          const count = getAgentStat(name, 'execution_count', 0)
          const latency = getAgentStat(name, 'average_latency_ms', 0.0).toFixed(1)
          const tokens = getAgentStat(name, 'total_tokens', 0)
          const cost = getAgentStat(name, 'estimated_cost', 0.0).toFixed(4)
          const failures = getAgentStat(name, 'failures', 0)
          const serviceCalls = getAgentStat(name, 'downstream_service_calls', 0)

          return (
            <Card key={name} className="border border-slate-200 shadow-sm bg-white overflow-hidden">
              <CardHeader className="pb-2 border-b border-slate-100 bg-slate-50/50">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Icon className="h-5 w-5 text-teal-600" />
                    <CardTitle className="text-sm font-bold text-slate-800 tracking-tight">{display}</CardTitle>
                  </div>
                  <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-100 text-indigo-800 rounded-full">
                    Operational
                  </span>
                </div>
              </CardHeader>
              <CardContent className="pt-4 grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Executions</span>
                  <span className="text-lg font-bold text-slate-900">{count}</span>
                  <span className="text-[10px] text-red-500 block">Failures: {failures}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Avg Latency</span>
                  <span className="text-lg font-bold text-slate-900">{latency} ms</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Total Tokens</span>
                  <span className="text-sm font-bold text-slate-900">{tokens.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Service Calls</span>
                  <span className="text-sm font-bold text-slate-900">{serviceCalls} calls</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Control console */}
      <Card className="border border-slate-200 shadow-md overflow-hidden bg-white">
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setActivePlayground('reminder')}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
              activePlayground === 'reminder'
                ? 'border-teal-600 text-teal-600 bg-slate-50/30'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Bell className="h-4 w-4" />
            Reminder Playground
          </button>
          <button
            onClick={() => setActivePlayground('appointment')}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
              activePlayground === 'appointment'
                ? 'border-teal-600 text-teal-600 bg-slate-50/30'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Calendar className="h-4 w-4" />
            Appointment Playground
          </button>
          <div className="flex-1 flex justify-end items-center px-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchStats()}
              className="text-xs flex items-center gap-1.5"
              disabled={statsLoading}
            >
              <RefreshCw className={`h-3 w-3 ${statsLoading ? 'animate-spin' : ''}`} />
              Refresh Metrics
            </Button>
          </div>
        </div>

        <CardContent className="p-6">
          {activePlayground === 'reminder' ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Input column */}
              <div className="space-y-6">
                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Patient Mongo ID</label>
                  <Input 
                    value={reminderPatientId} 
                    onChange={(e) => setReminderPatientId(e.target.value)} 
                    placeholder="Patient MongoDB ID"
                    className="font-mono text-sm bg-slate-50"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Prompt / Query Request</label>
                  <Textarea
                    value={reminderQuery}
                    onChange={(e) => setReminderQuery(e.target.value)}
                    rows={4}
                    placeholder="E.g., Create reminder to take Metformin 500mg daily at 8 PM..."
                    className="font-sans text-sm resize-none"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="reminderDebugCheck"
                    checked={reminderDebug}
                    onChange={(e) => setReminderDebug(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <label htmlFor="reminderDebugCheck" className="text-sm text-slate-600 font-medium select-none cursor-pointer">
                    Enable verbose drug safety checking logs
                  </label>
                </div>
                <Button 
                  onClick={handleTestReminder} 
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold flex items-center justify-center gap-2 shadow-sm"
                  disabled={reminderMutation.isPending}
                >
                  {reminderMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Orchestrating Service Operations...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-current" />
                      Run Reminder Agent
                    </>
                  )}
                </Button>
              </div>

              {/* Output Column */}
              <div className="border border-slate-100 rounded-lg p-6 bg-slate-50/40 space-y-6">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Agent Execution Results</h3>
                
                {reminderMutation.isIdle && (
                  <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                    <Info className="h-8 w-8 mb-2 stroke-1" />
                    <p className="text-sm">Run a reminder operation test to inspect RAG pipeline outputs and Mongo updates.</p>
                  </div>
                )}

                {reminderMutation.isPending && (
                  <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                    <RefreshCw className="h-8 w-8 mb-2 animate-spin text-teal-600" />
                    <p className="text-sm font-medium text-slate-600">Invoking Drug Safety Agent & creating database schedules...</p>
                  </div>
                )}

                {reminderMutation.isSuccess && (
                  <div className="space-y-6">
                    {/* Status card */}
                    <div className={`p-4 rounded-lg flex items-start gap-3 border ${
                      reminderMutation.data.status === 'failed'
                        ? 'bg-red-50 border-red-200 text-red-800'
                        : reminderMutation.data.status === 'warned'
                        ? 'bg-amber-50 border-amber-200 text-amber-800'
                        : 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    }`}>
                      {reminderMutation.data.status === 'failed' ? (
                        <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                      ) : reminderMutation.data.status === 'warned' ? (
                        <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      )}
                      <div>
                        <div className="font-bold text-sm capitalize">Action Status: {reminderMutation.data.status}</div>
                        <div className="text-xs opacity-90 mt-1">Matched Action: {reminderMutation.data.action}</div>
                        <div className="text-sm mt-2 font-medium">{reminderMutation.data.message}</div>
                      </div>
                    </div>

                    {/* Safety check warning if present */}
                    {reminderMutation.data.warnings && reminderMutation.data.warnings.length > 0 && (
                      <div className="p-4 bg-amber-50/50 border border-amber-200 rounded-lg">
                        <h4 className="text-xs font-bold text-amber-800 uppercase flex items-center gap-1.5 mb-2">
                          <AlertTriangle className="h-4 w-4 text-amber-600" />
                          Clinical Warnings Detected
                        </h4>
                        <ul className="list-disc pl-4 space-y-1 text-xs text-amber-800 font-medium">
                          {reminderMutation.data.warnings.map((w, idx) => (
                            <li key={idx}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Created entity JSON */}
                    {reminderMutation.data.created_reminder && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-slate-500 block uppercase">Created Reminder Reference</span>
                        <pre className="bg-slate-900 text-teal-400 p-4 rounded-lg text-xs font-mono overflow-auto max-h-48">
                          {JSON.stringify(reminderMutation.data.created_reminder, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Debug logs toggle info */}
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-500 block uppercase">Token Usage & Logs</span>
                      <div className="text-xs text-slate-500 bg-slate-100 p-3 rounded-md grid grid-cols-3 gap-2">
                        <div>Prompt: {reminderMutation.data.usage?.prompt_tokens ?? 0}</div>
                        <div>Completion: {reminderMutation.data.usage?.completion_tokens ?? 0}</div>
                        <div>Total: {reminderMutation.data.usage?.total_tokens ?? 0}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Input column */}
              <div className="space-y-6">
                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Patient Mongo ID</label>
                  <Input 
                    value={appointmentPatientId} 
                    onChange={(e) => setAppointmentPatientId(e.target.value)} 
                    placeholder="Patient MongoDB ID"
                    className="font-mono text-sm bg-slate-50"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 block uppercase mb-2">Prompt / Query Request</label>
                  <Textarea
                    value={appointmentQuery}
                    onChange={(e) => setAppointmentQuery(e.target.value)}
                    rows={4}
                    placeholder="E.g., Find cardiologist profile and book availability slot 65f7c..."
                    className="font-sans text-sm resize-none"
                  />
                </div>
                <Button 
                  onClick={handleTestAppointment} 
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold flex items-center justify-center gap-2 shadow-sm"
                  disabled={appointmentMutation.isPending}
                >
                  {appointmentMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Evaluating slot availabilities...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-current" />
                      Run Appointment Agent
                    </>
                  )}
                </Button>
              </div>

              {/* Output Column */}
              <div className="border border-slate-100 rounded-lg p-6 bg-slate-50/40 space-y-6">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Agent Execution Results</h3>

                {appointmentMutation.isIdle && (
                  <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                    <Info className="h-8 w-8 mb-2 stroke-1" />
                    <p className="text-sm">Run appointment operations test to query slot schedules and check booking locks.</p>
                  </div>
                )}

                {appointmentMutation.isPending && (
                  <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                    <RefreshCw className="h-8 w-8 mb-2 animate-spin text-teal-600" />
                    <p className="text-sm font-medium text-slate-600">Resolving doctor availability locks and slots calendar...</p>
                  </div>
                )}

                {appointmentMutation.isSuccess && (
                  <div className="space-y-6">
                    {/* Status badge */}
                    <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-start gap-3">
                      <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <div className="font-bold text-sm">Action: {appointmentMutation.data.action}</div>
                        <div className="text-sm mt-2 font-medium">{appointmentMutation.data.message}</div>
                        {appointmentMutation.data.reasoning && (
                          <div className="text-xs opacity-95 bg-emerald-100/50 p-2 rounded mt-2 border border-emerald-200/50 font-sans">
                            Reasoning: {appointmentMutation.data.reasoning}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Search results */}
                    {appointmentMutation.data.search_results && appointmentMutation.data.search_results.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-slate-500 block uppercase">Found Doctor Recommendations</span>
                        <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                          {appointmentMutation.data.search_results.map((doc: any, index: number) => (
                            <div key={index} className="p-3 bg-white border border-slate-200 rounded-md text-xs space-y-1 shadow-sm">
                              <div className="font-bold text-slate-800">{doc.name} - {doc.specialization}</div>
                              <div className="text-slate-500">{doc.hospital} | Fee: INR {doc.consultation_fee}</div>
                              <div className="text-[10px] text-slate-400 font-mono">Profile ID: {doc.id}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Slots list */}
                    {appointmentMutation.data.slots && appointmentMutation.data.slots.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-slate-500 block uppercase">Available Calendar Slots</span>
                        <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                          {appointmentMutation.data.slots.map((slot: any, index: number) => (
                            <div key={index} className="p-2 bg-teal-50/50 border border-teal-200 text-teal-800 rounded text-xs">
                              <div>Date: {slot.date}</div>
                              <div className="font-bold">Time: {slot.start_time} - {slot.end_time}</div>
                              <div className="text-[9px] text-teal-600 font-mono">Slot ID: {slot.id}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Booked Appointment */}
                    {appointmentMutation.data.appointment && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-slate-500 block uppercase">Appointment Reference Details</span>
                        <pre className="bg-slate-900 text-teal-400 p-4 rounded-lg text-xs font-mono overflow-auto max-h-48">
                          {JSON.stringify(appointmentMutation.data.appointment, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Rescheduled Appointment */}
                    {appointmentMutation.data.rescheduled_appointment && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-slate-500 block uppercase">Rescheduled Appointment Reference</span>
                        <pre className="bg-slate-900 text-teal-400 p-4 rounded-lg text-xs font-mono overflow-auto max-h-48">
                          {JSON.stringify(appointmentMutation.data.rescheduled_appointment, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
