import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { 
  useReportAgentTest, 
  useDrugAgentTest, 
  useDoctorAgentTest, 
  useHealthcareAgentsStatistics 
} from '@/hooks/use-ai'
import { 
  RefreshCw, 
  FileText, 
  ShieldAlert, 
  UserPlus, 
  Brain, 
  AlertTriangle, 
  AlertCircle 
} from 'lucide-react'

export function HealthcareAgentsView() {
  const [activePlayground, setActivePlayground] = useState<'report' | 'drug' | 'doctor'>('report')
  
  const [reportQuery, setReportQuery] = useState('Analyze my recent lipid panel report and explain the cholesterol levels.')
  const [reportPatientId, setReportPatientId] = useState('65f7c32b5e28a425fca68341')
  const [reportDebug, setReportDebug] = useState(false)
  
  const [drugQuery, setDrugQuery] = useState('Can I take Aspirin with Ibuprofen?')
  const [drugPatientId, setDrugPatientId] = useState('65f7c32b5e28a425fca68341')
  
  const [doctorQuery, setDoctorQuery] = useState('I need a cardiologist for chest pain.')
  const [doctorPatientId, setDoctorPatientId] = useState('65f7c32b5e28a425fca68341')

  const reportMutation = useReportAgentTest()
  const drugMutation = useDrugAgentTest()
  const doctorMutation = useDoctorAgentTest()
  
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useHealthcareAgentsStatistics()

  const handleTestReport = () => {
    reportMutation.mutate({
      query: reportQuery,
      patient_id: reportPatientId || undefined,
      debug_mode: reportDebug
    })
  }

  const handleTestDrug = () => {
    drugMutation.mutate({
      query: drugQuery,
      patient_id: drugPatientId || undefined
    })
  }

  const handleTestDoctor = () => {
    doctorMutation.mutate({
      query: doctorQuery,
      patient_id: doctorPatientId || undefined
    })
  }

  // Helper to safely fetch metrics per agent
  const getAgentStat = (agentName: string, metric: string, defaultValue: any = 0) => {
    if (!stats || !stats[agentName]) return defaultValue
    return stats[agentName][metric] ?? defaultValue
  }

  return (
    <div className="space-y-6">
      {/* Overview stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { name: 'ReportAnalysisAgent', display: 'Report Analysis' },
          { name: 'DrugInteractionAgent', display: 'Drug Safety & Interaction' },
          { name: 'DoctorRecommendationAgent', display: 'Doctor Recommendations' }
        ].map(({ name, display }) => {
          const count = getAgentStat(name, 'execution_count', 0)
          const latency = getAgentStat(name, 'average_latency_ms', 0.0).toFixed(1)
          const tokens = getAgentStat(name, 'total_tokens', 0)
          const cost = getAgentStat(name, 'estimated_cost', 0.0).toFixed(4)
          const failures = getAgentStat(name, 'failures', 0)
          const citations = getAgentStat(name, 'citation_count', 0)
          
          return (
            <Card key={name} className="border border-slate-200 shadow-sm bg-white overflow-hidden">
              <CardHeader className="pb-2 border-b border-slate-100 bg-slate-50/50">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-sm font-bold text-slate-800 tracking-tight">{display}</CardTitle>
                  <span className="px-2 py-0.5 text-[10px] font-semibold bg-blue-100 text-blue-800 rounded-full">
                    Healthcare
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
                  <span className="text-xs text-slate-400 block uppercase font-semibold">Tokens (Citations)</span>
                  <span className="text-sm font-bold text-slate-900">{tokens.toLocaleString()} ({citations})</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block uppercase font-semibold">LLM Cost</span>
                  <span className="text-sm font-bold text-slate-900">${cost}</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Main Console */}
      <Card className="border border-slate-200 shadow-md overflow-hidden bg-white">
        <CardHeader className="pb-0 border-b border-slate-100 bg-slate-50/50">
          <div className="flex justify-between items-center">
            <div className="flex gap-4">
              <button
                onClick={() => setActivePlayground('report')}
                className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                  activePlayground === 'report'
                    ? 'border-teal-600 text-teal-600 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Report Analysis
              </button>
              <button
                onClick={() => setActivePlayground('drug')}
                className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                  activePlayground === 'drug'
                    ? 'border-teal-600 text-teal-600 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Drug Safety Check
              </button>
              <button
                onClick={() => setActivePlayground('doctor')}
                className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                  activePlayground === 'doctor'
                    ? 'border-teal-600 text-teal-600 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Doctor Referrals
              </button>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchStats()}
              disabled={statsLoading}
              className="mb-2 text-xs flex items-center gap-1.5"
            >
              <RefreshCw className={`h-3 w-3 ${statsLoading ? 'animate-spin' : ''}`} />
              Refresh Stats
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          
          {/* Report Analysis Playground */}
          {activePlayground === 'report' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h3 className="text-md font-bold text-slate-800 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-teal-600" />
                  Report Analysis Playground
                </h3>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500">Query prompt / Question</label>
                  <Textarea
                    value={reportQuery}
                    onChange={(e) => setReportQuery(e.target.value)}
                    rows={4}
                    placeholder="Enter question about report..."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500">Patient MongoDB ID reference</label>
                  <Input
                    value={reportPatientId}
                    onChange={(e) => setReportPatientId(e.target.value)}
                    placeholder="Patient ID..."
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="reportDebug"
                    checked={reportDebug}
                    onChange={(e) => setReportDebug(e.target.checked)}
                    className="h-4 w-4 border-slate-300 rounded text-teal-600"
                  />
                  <label htmlFor="reportDebug" className="text-xs font-semibold text-slate-500 cursor-pointer">
                    Enable verbose debug parameters
                  </label>
                </div>
                <Button
                  onClick={handleTestReport}
                  disabled={reportMutation.isPending}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold"
                >
                  {reportMutation.isPending ? 'Executing Agent...' : 'Submit Report Inquiry'}
                </Button>
              </div>

              {/* Response Display */}
              <div className="space-y-4">
                <span className="text-sm font-bold text-slate-800 block">Agent Execution Outcomes</span>
                
                {reportMutation.isPending ? (
                  <div className="h-[300px] border border-slate-200 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2 bg-slate-50/50">
                    <RefreshCw className="h-8 w-8 text-teal-600 animate-spin" />
                    <span className="text-sm">Orchestrating Report RAG workflow...</span>
                  </div>
                ) : reportMutation.isSuccess ? (
                  <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                    {/* Metadata Card */}
                    <div className="grid grid-cols-3 gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-xs">
                      <div>
                        <span className="text-slate-400 block uppercase font-bold text-[9px]">Latency</span>
                        <span className="font-semibold text-slate-800">
                          {reportMutation.data.metadata?.total_latency_ms?.toFixed(1) || 0} ms
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-bold text-[9px]">Groq Latency</span>
                        <span className="font-semibold text-slate-800">
                          {reportMutation.data.metadata?.groq_latency_ms?.toFixed(1) || 0} ms
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-bold text-[9px]">Tokens Used</span>
                        <span className="font-semibold text-slate-800">
                          {reportMutation.data.usage?.total_tokens || 0}
                        </span>
                      </div>
                    </div>

                    {/* Summary */}
                    <div className="p-3 bg-teal-50/50 rounded-lg border border-teal-100 text-sm">
                      <span className="font-bold text-teal-900 block mb-1">Summary Explanation</span>
                      <p className="text-slate-700 leading-relaxed">{reportMutation.data.summary}</p>
                    </div>

                    {/* Key Findings */}
                    {reportMutation.data.key_findings?.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-slate-500 block uppercase">Key Findings</span>
                        <ul className="list-disc pl-4 text-sm text-slate-700 space-y-0.5">
                          {reportMutation.data.key_findings.map((f, i) => (
                            <li key={i}>{f}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Abnormal Metrics */}
                    {reportMutation.data.abnormal_values?.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-bold text-slate-500 block uppercase">Detected Abnormal Values</span>
                        <div className="border border-slate-150 rounded-md overflow-hidden bg-white">
                          <table className="min-w-full text-xs text-left">
                            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-150">
                              <tr>
                                <th className="px-3 py-1.5">Metric</th>
                                <th className="px-3 py-1.5">Observed</th>
                                <th className="px-3 py-1.5">Reference Range</th>
                                <th className="px-3 py-1.5">Status</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 text-slate-700">
                              {reportMutation.data.abnormal_values.map((v, i) => (
                                <tr key={i} className="hover:bg-slate-50/50">
                                  <td className="px-3 py-1.5 font-semibold text-slate-800">{v.metric}</td>
                                  <td className="px-3 py-1.5 text-red-600 font-bold">{v.value}</td>
                                  <td className="px-3 py-1.5 text-slate-500">{v.normal_range}</td>
                                  <td className="px-3 py-1.5">
                                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 uppercase">
                                      {v.status}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Trends */}
                    {reportMutation.data.trend_analysis?.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-slate-500 block uppercase">Historical Trends Comparison</span>
                        <ul className="list-disc pl-4 text-sm text-slate-700 space-y-0.5">
                          {reportMutation.data.trend_analysis.map((t, i) => (
                            <li key={i}>{t}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Recommendations */}
                    {reportMutation.data.recommendations?.length > 0 && (
                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-sm">
                        <span className="font-bold text-slate-800 block mb-1">Informational Recommendations</span>
                        <ul className="list-disc pl-4 text-xs text-slate-600 space-y-1">
                          {reportMutation.data.recommendations.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Citations */}
                    {reportMutation.data.citations?.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-bold text-slate-500 block uppercase">Evidence Citations</span>
                        <div className="space-y-1 text-xs">
                          {reportMutation.data.citations.map((c, i) => (
                            <div key={i} className="p-2 bg-slate-50 border border-slate-200 rounded-md">
                              <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                                <span className="font-bold uppercase">Source: {c.source}</span>
                                <span className="font-semibold">Match score: {(c.score * 100).toFixed(0)}%</span>
                              </div>
                              <p className="text-slate-600 leading-relaxed italic">&ldquo;{c.text}&rdquo;</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Debug JSON */}
                    <div className="space-y-1">
                      <span className="text-xs font-bold text-slate-500 block uppercase">Raw Response Trace</span>
                      <pre className="p-2 text-[10px] text-teal-800 bg-teal-50 border border-teal-100 rounded-md overflow-x-auto">
                        {JSON.stringify(reportMutation.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : reportMutation.isError ? (
                  <div className="p-3 border border-red-200 bg-red-50 text-red-800 rounded-lg text-sm flex gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0" />
                    <span>{(reportMutation.error as Error).message}</span>
                  </div>
                ) : (
                  <div className="h-[300px] border border-dashed border-slate-300 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2">
                    <Brain className="h-10 w-10 text-slate-300" />
                    <span className="text-sm font-semibold">Ready to analyze reports. Submit a query.</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Drug Safety Playground */}
          {activePlayground === 'drug' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h3 className="text-md font-bold text-slate-800 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-red-600" />
                  Medication Interaction & Safety Playground
                </h3>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500">Query medications / substances</label>
                  <Textarea
                    value={drugQuery}
                    onChange={(e) => setDrugQuery(e.target.value)}
                    rows={4}
                    placeholder="Enter medications query (e.g. Can I take Metformin with Ibuprofen?)..."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500">Patient ID (MongoDB lookup memory context)</label>
                  <Input
                    value={drugPatientId}
                    onChange={(e) => setDrugPatientId(e.target.value)}
                    placeholder="Patient ID..."
                  />
                </div>
                <Button
                  onClick={handleTestDrug}
                  disabled={drugMutation.isPending}
                  className="w-full bg-red-600 hover:bg-red-700 text-white font-bold"
                >
                  {drugMutation.isPending ? 'Checking drug conflicts...' : 'Validate Medication Safety'}
                </Button>
              </div>

              {/* Response Display */}
              <div className="space-y-4">
                <span className="text-sm font-bold text-slate-800 block">Agent Execution Outcomes</span>
                
                {drugMutation.isPending ? (
                  <div className="h-[300px] border border-slate-200 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2 bg-slate-50/50">
                    <RefreshCw className="h-8 w-8 text-red-600 animate-spin" />
                    <span className="text-sm">Assessing drug-drug & allergy contraindications...</span>
                  </div>
                ) : drugMutation.isSuccess ? (
                  <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                    {/* Severity Badge */}
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-400 block uppercase">Interaction Risk Assessment</span>
                      <span className={`px-3 py-1 text-xs font-bold uppercase rounded-full ${
                        drugMutation.data.severity === 'CRITICAL'
                          ? 'bg-red-200 text-red-900 border border-red-300'
                          : drugMutation.data.severity === 'HIGH'
                          ? 'bg-orange-200 text-orange-950 border border-orange-300'
                          : drugMutation.data.severity === 'MEDIUM'
                          ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-250'
                      }`}>
                        Severity: {drugMutation.data.severity}
                      </span>
                    </div>

                    {/* Summary */}
                    <div className="p-3 bg-red-50/50 border border-red-100 rounded-lg text-sm">
                      <span className="font-bold text-red-900 block mb-1">Safety Diagnostic Narrative</span>
                      <p className="text-slate-700 leading-relaxed">{drugMutation.data.interaction_summary}</p>
                    </div>

                    {/* Warnings List */}
                    {drugMutation.data.warnings?.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-500 block uppercase">Identified Safety Warnings</span>
                        <div className="space-y-1.5">
                          {drugMutation.data.warnings.map((w, i) => (
                            <div key={i} className="p-2 border border-orange-200 bg-orange-50/30 rounded-md text-xs text-orange-950 flex gap-2">
                              <AlertCircle className="h-4 w-4 text-orange-700 flex-shrink-0" />
                              <span>{w}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Alternatives */}
                    {drugMutation.data.alternatives?.length > 0 && (
                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-sm">
                        <span className="font-bold text-slate-800 block mb-1">Medication Alternatives to Discuss</span>
                        <ul className="list-disc pl-4 text-xs text-slate-600 space-y-1">
                          {drugMutation.data.alternatives.map((a, i) => (
                            <li key={i}>{a}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Citations */}
                    {drugMutation.data.citations?.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-bold text-slate-500 block uppercase">Safety Knowledge Citations</span>
                        <div className="space-y-1 text-xs">
                          {drugMutation.data.citations.map((c, i) => (
                            <div key={i} className="p-2 bg-slate-50 border border-slate-200 rounded-md">
                              <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                                <span className="font-bold uppercase">Source: {c.source}</span>
                                <span className="font-semibold">Match score: {(c.score * 100).toFixed(0)}%</span>
                              </div>
                              <p className="text-slate-600 leading-relaxed italic">&ldquo;{c.text}&rdquo;</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Debug JSON */}
                    <div className="space-y-1">
                      <span className="text-xs font-bold text-slate-500 block uppercase">Raw Diagnostic Trace</span>
                      <pre className="p-2 text-[10px] text-red-800 bg-red-50 border border-red-100 rounded-md overflow-x-auto">
                        {JSON.stringify(drugMutation.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : drugMutation.isError ? (
                  <div className="p-3 border border-red-200 bg-red-50 text-red-800 rounded-lg text-sm flex gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0" />
                    <span>{(drugMutation.error as Error).message}</span>
                  </div>
                ) : (
                  <div className="h-[300px] border border-dashed border-slate-300 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2">
                    <Brain className="h-10 w-10 text-slate-300" />
                    <span className="text-sm font-semibold">Ready to validate medication safety. Submit a query.</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Doctor Recommendation Playground */}
          {activePlayground === 'doctor' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h3 className="text-md font-bold text-slate-800 flex items-center gap-2">
                  <UserPlus className="h-5 w-5 text-blue-600" />
                  Doctor Referrals & Matcher Playground
                </h3>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500">Query symptoms / specialist request</label>
                  <Textarea
                    value={doctorQuery}
                    onChange={(e) => setDoctorQuery(e.target.value)}
                    rows={4}
                    placeholder="Enter symptoms or doctor requests..."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500">Patient ID (MongoDB lookup location context)</label>
                  <Input
                    value={doctorPatientId}
                    onChange={(e) => setDoctorPatientId(e.target.value)}
                    placeholder="Patient ID..."
                  />
                </div>
                <Button
                  onClick={handleTestDoctor}
                  disabled={doctorMutation.isPending}
                  className="w-full bg-blue-650 hover:bg-blue-750 text-white font-bold"
                >
                  {doctorMutation.isPending ? 'Matching doctors...' : 'Match Suitable Specialists'}
                </Button>
              </div>

              {/* Response Display */}
              <div className="space-y-4">
                <span className="text-sm font-bold text-slate-800 block">Agent Execution Outcomes</span>
                
                {doctorMutation.isPending ? (
                  <div className="h-[300px] border border-slate-200 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2 bg-slate-50/50">
                    <RefreshCw className="h-8 w-8 text-blue-600 animate-spin" />
                    <span className="text-sm">Matching profiles and checking active slots...</span>
                  </div>
                ) : doctorMutation.isSuccess ? (
                  <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                    
                    {/* General recommendation metrics */}
                    <div className="grid grid-cols-2 gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-xs">
                      <div>
                        <span className="text-slate-400 block uppercase font-bold text-[9px]">Matched Specialty</span>
                        <span className="font-bold text-slate-800 uppercase">
                          {doctorMutation.data.matching_specialization}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase font-bold text-[9px]">Matching Confidence</span>
                        <span className="font-bold text-slate-800">
                          {(doctorMutation.data.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Reasoning */}
                    <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-lg text-sm">
                      <span className="font-bold text-blue-900 block mb-1">Referral Reasoning</span>
                      <p className="text-slate-700 leading-relaxed">{doctorMutation.data.reasoning}</p>
                    </div>

                    {/* Doctor Recommendation Cards */}
                    {doctorMutation.data.recommended_doctors?.length > 0 ? (
                      <div className="space-y-3">
                        <span className="text-xs font-bold text-slate-500 block uppercase">Recommended Clinicians</span>
                        {doctorMutation.data.recommended_doctors.map((d, i) => (
                          <div key={i} className="border border-slate-200 rounded-lg p-3 bg-white hover:shadow-sm transition-shadow">
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-bold text-slate-850 text-sm">{d.full_name}</h4>
                                <span className="text-xs text-teal-700 font-semibold">{d.specialization}</span>
                              </div>
                              <span className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full">
                                {d.experience_years} years exp
                              </span>
                            </div>
                            <div className="mt-2 space-y-1 text-xs text-slate-600 border-t border-slate-100 pt-2">
                              <div className="flex justify-between">
                                <span className="font-semibold text-slate-400">Hospital:</span>
                                <span>{d.hospital}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="font-semibold text-slate-400">Languages:</span>
                                <span>{Array.isArray(d.languages) ? d.languages.join(', ') : d.languages}</span>
                              </div>
                              <div className="flex justify-between items-center text-teal-800 font-bold bg-teal-50 px-2 py-1 rounded mt-1.5">
                                <span className="text-[10px] text-teal-600 uppercase">Availability:</span>
                                <span className="text-[10px]">{d.availability}</span>
                              </div>
                              <div className="mt-2 text-slate-700 leading-relaxed p-2 bg-slate-50 rounded italic text-[11px] border border-slate-100">
                                <span className="font-bold text-slate-500 block not-italic text-[9px] uppercase mb-0.5">Clinical reasoning:</span>
                                &ldquo;{d.match_reason}&rdquo;
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-3 border border-yellow-200 bg-yellow-50 text-yellow-800 rounded-lg text-xs flex gap-2">
                        <AlertTriangle className="h-4 w-4 text-yellow-600 flex-shrink-0" />
                        <span>No doctors matched symptoms in the vector space. Please try rephrasing query.</span>
                      </div>
                    )}

                    {/* Debug JSON */}
                    <div className="space-y-1">
                      <span className="text-xs font-bold text-slate-500 block uppercase">Raw Referral Trace</span>
                      <pre className="p-2 text-[10px] text-blue-800 bg-blue-50 border border-blue-100 rounded-md overflow-x-auto">
                        {JSON.stringify(doctorMutation.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : doctorMutation.isError ? (
                  <div className="p-3 border border-red-200 bg-red-50 text-red-800 rounded-lg text-sm flex gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0" />
                    <span>{(doctorMutation.error as Error).message}</span>
                  </div>
                ) : (
                  <div className="h-[300px] border border-dashed border-slate-300 rounded-lg flex flex-col justify-center items-center text-slate-400 gap-2">
                    <Brain className="h-10 w-10 text-slate-300" />
                    <span className="text-sm font-semibold">Ready to recommend matching specialists. Submit a query.</span>
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
