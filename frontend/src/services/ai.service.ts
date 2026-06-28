import { apiClient } from '@/lib/axios'

export interface AIHealthResponse {
  reachable: boolean
  model: string
  latency_ms: number
  status: string
  timestamp: string
}

export interface AITestResponse {
  response: string
  model: string
  token_usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  latency: number
  finish_reason: string
}

export interface EmbeddingHealthResponse {
  provider: string
  model: string
  dimensions: number
  latency: number
  status: string
}

export interface EmbeddingTestResponse {
  dimensions: number
  vector_preview: number[]
  latency: number
  metadata: Record<string, any>
}

export interface VectorCollectionInfo {
  name: string
  status: string
  vector_count: number
  dimensions: number
  distance: string
  storage_bytes?: number
  last_update_time?: string
}

export interface VectorHealthResponse {
  connected: boolean
  latency: number
  collections: VectorCollectionInfo[]
}

export interface VectorTestResultItem {
  id: string
  score: number
  payload: Record<string, any>
}

export interface VectorTestResponse {
  latency: number
  search_results: VectorTestResultItem[]
  similarity_scores: number[]
}

export interface PatientContextMetadata {
  patient_id: string
  generated_at: string
  sources_used: string[]
  sections_returned: string[]
  estimated_tokens: number
  context_version: string
}

export interface PatientContextResponse {
  patient_profile?: Record<string, any>
  medical_summary?: string
  current_conditions: string[]
  past_medical_history: string[]
  current_medications: string[]
  medication_allergies: string[]
  drug_allergies: string[]
  lab_reports_summary: Record<string, any>[]
  appointments_summary: Record<string, any>[]
  consultations_summary: Record<string, any>[]
  prescriptions_summary: Record<string, any>[]
  reminder_summary: Record<string, any>[]
  recent_health_insights: Record<string, any>[]
  lifestyle_notes?: string
  emergency_information?: string
  risk_factors: string[]
  metadata: PatientContextMetadata
}

export const aiService = {
  /**
   * Retrieves connectivity and latency details from the AI backend health check.
   */
  getAIHealth: async (): Promise<AIHealthResponse> => {
    const response = await apiClient.get<AIHealthResponse>('/ai/health')
    return response.data
  },

  /**
   * Executes a direct prompt completion verification test. Admin accounts only.
   */
  testAIPlayground: async (prompt: string): Promise<AITestResponse> => {
    const response = await apiClient.post<AITestResponse>('/ai/test', { prompt })
    return response.data
  },

  /**
   * Retrieves connectivity details from the AI embedding health check.
   */
  getEmbeddingHealth: async (): Promise<EmbeddingHealthResponse> => {
    const response = await apiClient.get<EmbeddingHealthResponse>('/ai/embeddings/health')
    return response.data
  },

  /**
   * Generates a preview embedding and metadata. Admin accounts only.
   */
  testEmbeddingPlayground: async (text: string): Promise<EmbeddingTestResponse> => {
    const response = await apiClient.post<EmbeddingTestResponse>('/ai/embeddings/test', { text })
    return response.data
  },

  /**
   * Retrieves overall vector health status and collection stats. Admin accounts only.
   */
  getVectorHealth: async (): Promise<VectorHealthResponse> => {
    const response = await apiClient.get<VectorHealthResponse>('/ai/vector/health')
    return response.data
  },

  /**
   * Retrieves list of Qdrant collection specifications. Admin accounts only.
   */
  getVectorCollections: async (): Promise<VectorCollectionInfo[]> => {
    const response = await apiClient.get<VectorCollectionInfo[]>('/ai/vector/collections')
    return response.data
  },

  /**
   * Executes a roundtrip semantic query verification test. Admin accounts only.
   */
  testVectorSearch: async (collection: string, text: string): Promise<VectorTestResponse> => {
    const response = await apiClient.post<VectorTestResponse>('/ai/vector/test', { collection, text })
    return response.data
  },

  /**
   * Assembles a patient's complete structured AI context. Admin/Doctor accounts only (or Patient /context/me).
   */
  getPatientContext: async (patientId?: string): Promise<PatientContextResponse> => {
    const url = patientId ? `/ai/context/${patientId}` : '/ai/context/me'
    const response = await apiClient.get<PatientContextResponse>(url)
    return response.data
  },

  /**
   * Retrieves overall status details of the integrated AI infrastructure health check. Admin only.
   */
  getAIPlaygroundHealth: async (): Promise<AIPlaygroundHealthResponse> => {
    const response = await apiClient.get<AIPlaygroundHealthResponse>('/ai/playground/health')
    return response.data
  },

  /**
   * Executes a playground chat session query with optional patient context. Admin only.
   */
  testAIPlaygroundChat: async (request: AIPlaygroundChatRequest): Promise<AIPlaygroundChatResponse> => {
    const response = await apiClient.post<AIPlaygroundChatResponse>('/ai/playground/chat', request)
    return response.data
  },

  /**
   * Index a single document. Admin accounts only.
   */
  indexDocument: async (request: DocumentIndexRequest): Promise<DocumentIndexResponse> => {
    const response = await apiClient.post<DocumentIndexResponse>('/ai/index', request)
    return response.data
  },

  /**
   * Index multiple documents in a batch. Admin accounts only.
   */
  batchIndexDocuments: async (request: BatchDocumentIndexRequest): Promise<BatchDocumentIndexResponse> => {
    const response = await apiClient.post<BatchDocumentIndexResponse>('/ai/batch-index', request)
    return response.data
  },

  /**
   * Reindex an existing document. Admin accounts only.
   */
  reindexDocument: async (request: DocumentIndexRequest): Promise<DocumentIndexResponse> => {
    const response = await apiClient.post<DocumentIndexResponse>('/ai/reindex', request)
    return response.data
  },

  /**
   * Remove a specific document from vector space. Admin accounts only.
   */
  deleteDocument: async (documentId: string, documentType: string): Promise<IndexDeletionResponse> => {
    const response = await apiClient.delete<IndexDeletionResponse>('/ai/document', {
      params: { document_id: documentId, document_type: documentType }
    })
    return response.data
  },

  /**
   * Remove all vectors for patient reports matching patient ID. Admin accounts only.
   */
  deletePatientDocuments: async (patientId: string): Promise<IndexDeletionResponse> => {
    const response = await apiClient.delete<IndexDeletionResponse>('/ai/patient', {
      params: { patient_id: patientId }
    })
    return response.data
  },

  /**
   * Retrieves overall document indexing statistics and model versions. Admin accounts only.
   */
  getIndexStatistics: async (): Promise<IndexingStatisticsResponse> => {
    const response = await apiClient.get<IndexingStatisticsResponse>('/ai/index/statistics')
    return response.data
  },

  retrieveSingle: async (request: RetrievalRequest): Promise<RetrievalResponse> => {
    const response = await apiClient.post<RetrievalResponse>('/ai/retrieve/single', request)
    return response.data
  },

  retrieveMulti: async (request: RetrievalRequest): Promise<RetrievalResponse> => {
    const response = await apiClient.post<RetrievalResponse>('/ai/retrieve/multi', request)
    return response.data
  },

  retrieveAgent: async (request: RetrievalRequest): Promise<RetrievalPackage> => {
    const response = await apiClient.post<RetrievalPackage>('/ai/retrieve', request)
    return response.data
  },

  retrieveAgentDebug: async (request: RetrievalRequest): Promise<RetrievalPackage> => {
    const response = await apiClient.post<RetrievalPackage>('/ai/retrieve/debug', request)
    return response.data
  },

  getRetrievalStatistics: async (): Promise<RetrievalAgentStatisticsResponse> => {
    const response = await apiClient.get<RetrievalAgentStatisticsResponse>('/ai/retrieve/statistics')
    return response.data
  },

  getRetrievalStatisticsRaw: async (): Promise<RetrievalStatisticsResponse> => {
    const response = await apiClient.get<RetrievalStatisticsResponse>('/ai/retrieve/statistics/raw')
    return response.data
  },

  buildContext: async (request: ContextAssemblyRequest): Promise<ContextAssemblyResponse> => {
    const response = await apiClient.post<ContextAssemblyResponse>('/ai/context/build', request)
    return response.data
  },

  getContextAssemblyStatistics: async (): Promise<ContextAssemblyStatisticsResponse> => {
    const response = await apiClient.get<ContextAssemblyStatisticsResponse>('/ai/context/statistics')
    return response.data
  },

  getSyncStatus: async (): Promise<SyncStatusResponse> => {
    const response = await apiClient.get<SyncStatusResponse>('/ai/sync/status')
    return response.data
  },

  syncPatient: async (patientId: string): Promise<SyncPatientResponse> => {
    const response = await apiClient.post<SyncPatientResponse>(`/ai/sync/patient/${patientId}`)
    return response.data
  },

  rebuildSync: async (): Promise<SyncRebuildResponse> => {
    const response = await apiClient.post<SyncRebuildResponse>('/ai/sync/rebuild')
    return response.data
  },

  getSyncStatistics: async (): Promise<SyncStatisticsResponse> => {
    const response = await apiClient.get<SyncStatisticsResponse>('/ai/sync/statistics')
    return response.data
  },

  getRagHealth: async (): Promise<RagHealthResponse> => {
    const response = await apiClient.get<RagHealthResponse>('/ai/rag/health')
    return response.data
  },

  getRagStatistics: async (): Promise<RagStatisticsResponse> => {
    const response = await apiClient.get<RagStatisticsResponse>('/ai/rag/statistics')
    return response.data
  },

  runRagBenchmark: async (patientId?: string, tokenBudget?: number, scoreThreshold?: number): Promise<RagBenchmarkResponse> => {
    const response = await apiClient.post<RagBenchmarkResponse>('/ai/rag/benchmark', {
      patient_id: patientId,
      token_budget: tokenBudget,
      score_threshold: scoreThreshold
    })
    return response.data
  },

  evaluateQuery: async (
    query: string,
    patientId?: string,
    collections?: string[],
    filters?: Record<string, any>,
    groundTruthDocIds?: string[],
    topK?: number,
    scoreThreshold?: number,
    tokenBudget?: number
  ): Promise<RagEvaluateResponse> => {
    const response = await apiClient.post<RagEvaluateResponse>('/ai/rag/evaluate', {
      query,
      patient_id: patientId,
      collections,
      filters,
      ground_truth_doc_ids: groundTruthDocIds,
      top_k: topK,
      score_threshold: scoreThreshold,
      token_budget: tokenBudget
    })
    return response.data
  },

  getGraphHealth: async (): Promise<GraphHealthResponse> => {
    const response = await apiClient.get<GraphHealthResponse>('/ai/graph/health')
    return response.data
  },

  getGraphNodes: async (): Promise<GraphNodesResponse> => {
    const response = await apiClient.get<GraphNodesResponse>('/ai/graph/nodes')
    return response.data
  },

  getGraphStatistics: async (): Promise<GraphStatisticsResponse> => {
    const response = await apiClient.get<GraphStatisticsResponse>('/ai/graph/statistics')
    return response.data
  },

  testGraphExecution: async (request: GraphTestRunRequest): Promise<GraphTestRunResponse> => {
    const response = await apiClient.post<GraphTestRunResponse>('/ai/graph/test', request)
    return response.data
  },

  getRouterIntents: async (): Promise<RouterIntentsResponse> => {
    const response = await apiClient.get<RouterIntentsResponse>('/ai/router/intents')
    return response.data
  },

  classifyRouterQuery: async (request: RouterClassifyRequest): Promise<RouterClassifyResponse> => {
    const response = await apiClient.post<RouterClassifyResponse>('/ai/router/classify', request)
    return response.data
  },

  testRouterPipeline: async (request: RouterTestRequest): Promise<RouterTestResponse> => {
    const response = await apiClient.post<RouterTestResponse>('/ai/router/test', request)
    return response.data
  },

  getRouterStatistics: async (): Promise<RouterStatisticsResponse> => {
    const response = await apiClient.get<RouterStatisticsResponse>('/ai/router/statistics')
    return response.data
  },

  testMedicalAgent: async (request: RouterTestRequest): Promise<MedicalKnowledgeAgentResponse> => {
    const response = await apiClient.post<MedicalKnowledgeAgentResponse>('/ai/agents/medical/test', request)
    return response.data
  },

  testSymptomAgent: async (request: RouterTestRequest): Promise<SymptomAgentResponse> => {
    const response = await apiClient.post<SymptomAgentResponse>('/ai/agents/symptom/test', request)
    return response.data
  },

  testMemoryAgent: async (request: RouterTestRequest): Promise<MemoryAgentResponse> => {
    const response = await apiClient.post<MemoryAgentResponse>('/ai/agents/memory/test', request)
    return response.data
  },

  getCoreAgentsStatistics: async (): Promise<Record<string, any>> => {
    const response = await apiClient.get<Record<string, any>>('/ai/agents/statistics')
    return response.data
  },

  testReportAnalysisAgent: async (request: RouterTestRequest): Promise<ReportAnalysisAgentResponse> => {
    const response = await apiClient.post<ReportAnalysisAgentResponse>('/ai/agents/report/test', request)
    return response.data
  },

  testDrugInteractionAgent: async (request: RouterTestRequest): Promise<DrugInteractionAgentResponse> => {
    const response = await apiClient.post<DrugInteractionAgentResponse>('/ai/agents/drug/test', request)
    return response.data
  },

  testDoctorRecommendationAgent: async (request: RouterTestRequest): Promise<DoctorRecommendationAgentResponse> => {
    const response = await apiClient.post<DoctorRecommendationAgentResponse>('/ai/agents/doctor/test', request)
    return response.data
  },

  getHealthcareAgentsStatistics: async (): Promise<Record<string, any>> => {
    const response = await apiClient.get<Record<string, any>>('/ai/agents/healthcare/statistics')
    return response.data
  },

  testReminderAgent: async (request: RouterTestRequest): Promise<ReminderAgentResponse> => {
    const response = await apiClient.post<ReminderAgentResponse>('/ai/agents/reminder/test', request)
    return response.data
  },

  testAppointmentAgent: async (request: RouterTestRequest): Promise<AppointmentAgentResponse> => {
    const response = await apiClient.post<AppointmentAgentResponse>('/ai/agents/appointment/test', request)
    return response.data
  },

  getOperationsAgentsStatistics: async (): Promise<Record<string, any>> => {
    const response = await apiClient.get<Record<string, any>>('/ai/agents/operations/statistics')
    return response.data
  },

  executeOrchestrator: async (request: AIExecuteRequest): Promise<StandardResponseContract> => {
    const response = await apiClient.post<StandardResponseContract>('/ai/execute', request)
    return response.data
  },

  debugOrchestrator: async (request: AIExecuteRequest): Promise<StandardResponseContract> => {
    const response = await apiClient.post<StandardResponseContract>('/ai/execution/debug', request)
    return response.data
  },

  getOrchestratorStatistics: async (): Promise<OrchestratorStatisticsResponse> => {
    const response = await apiClient.get<OrchestratorStatisticsResponse>('/ai/execution/statistics')
    return response.data
  },

  getOrchestratorHealth: async (): Promise<Record<string, any>> => {
    const response = await apiClient.get<Record<string, any>>('/ai/execution/health')
    return response.data
  },

  lookupDrug: async (drugName: string): Promise<DrugLookupResponse> => {
    const response = await apiClient.get<DrugLookupResponse>(`/ai/drug/lookup/${encodeURIComponent(drugName)}`)
    return response.data
  },

  normalizeDrug: async (drugName: string): Promise<DrugNormalizeResponse> => {
    const response = await apiClient.post<DrugNormalizeResponse>('/ai/drug/normalize', { drug_name: drugName })
    return response.data
  },

  getDrugStatistics: async (): Promise<DrugTelemetryResponse> => {
    const response = await apiClient.get<DrugTelemetryResponse>('/ai/drug/statistics')
    return response.data
  }
}

export interface AIPlaygroundChatRequest {
  prompt: string
  patient_id?: string
  model?: string
  temperature?: number
  max_tokens?: number
}

export interface AIExecutionSession {
  request_id: string
  user_id?: string
  patient_id?: string
  model: string
  start_time: string
  end_time: string
  duration: number
  tokens: number
  cost: number
  status: string
  errors?: string
}

export interface AIPlaygroundChatResponse {
  response: string
  execution_session: AIExecutionSession
  prompt_template: string
  patient_context_sections: string[]
}

export interface AIPlaygroundHealthResponse {
  groq: Record<string, any>
  embedding: Record<string, any>
  vector: Record<string, any>
  prompt_registry: Record<string, any>
  context_builder: Record<string, any>
}

export interface DocumentIndexRequest {
  document_id: string
  document_type: string
  content: string
  chunking_strategy?: string
  chunk_size?: number
  overlap?: number
  patient_id?: string
  report_id?: string
  page_number?: number
  section?: string
  source?: string
  language?: string
  created_by?: string
}

export interface DocumentIndexResponse {
  success: boolean
  document_id: string
  status: string
  chunks_count: number
  skipped_count?: number
  latency_ms?: number
  message?: string
  error?: string
}

export interface BatchDocumentIndexRequest {
  documents: DocumentIndexRequest[]
}

export interface BatchDocumentIndexResponse {
  results: DocumentIndexResponse[]
}

export interface IndexingStatisticsResponse {
  indexed_documents: number
  indexed_chunks: number
  duplicate_documents_skipped: number
  avg_chunk_size: number
  embedding_version: string
  index_version: number
  schema_version: number
}

export interface IndexDeletionResponse {
  success: boolean
  message?: string
}

export interface RetrievalRequest {
  query: string
  collection?: string
  collections?: string[]
  filters?: Record<string, any>
  top_k?: number
  score_threshold?: number
  patient_id?: string
  intent?: string
}

export interface RetrievalMatch {
  collection: string
  id: string
  score: number
  content: string
  metadata: Record<string, any>
  document_type: string
  patient_id?: string
  report_id?: string
  citations: Record<string, any>
}

export interface RetrievalResponse {
  results: RetrievalMatch[]
  retrieval_time: number
  collections_queried: string[]
  chunks_found: number
  duplicates_removed: number
}

export interface RetrievalStatisticsResponse {
  searches_executed: number
  failed_searches: number
  avg_latency_ms: number
  avg_score: number
  duplicate_chunks_removed: number
  timeout_count: number
}

export interface RetrievalPackage {
  intent: string
  collections_used: string[]
  retrieved_chunks: RetrievalMatch[]
  context: string
  citations: Record<string, {
    source?: string
    collection?: string
    document_id?: string
    chunk_id?: string
    page_number?: number
    score?: number
  }>
  metadata: Record<string, any>
  latency: Record<string, number>
  scores: Record<string, number>
  cache_status: string
}

export interface RetrievalAgentStatisticsResponse {
  requests: number
  failures: number
  cache_hits: number
  cache_misses: number
  cache_hit_ratio: number
  avg_retrieval_latency_ms: number
  avg_ranking_latency_ms: number
  avg_context_latency_ms: number
  avg_latency_ms: number
  intent_counts: Record<string, number>
  collection_usage: Record<string, number>
}

export interface ContextAssemblyRequest {
  query: string
  patient_id?: string
  token_budget?: number
  collections?: string[]
  filters?: Record<string, any>
}

export interface ContextAssemblyResponse {
  sections: Record<string, string>
  citations: Record<string, {
    source: string
    collection: string
    document_id: string
    chunk_id: string
    page_number: number
    score: number
  }>
  estimated_tokens: number
  compression_ratio: number
  assembly_time: number
  metadata: Record<string, any>
}

export interface ContextAssemblyStatisticsResponse {
  assemblies_executed: number
  failed_assemblies: number
  avg_latency_ms: number
  avg_compression_ratio: number
  avg_tokens_assembled: number
  total_original_chunks: number
  total_removed_chunks: number
  section_counts: Record<string, number>
}

export interface SyncStatusResponse {
  running: boolean
  queue_size: number
  dlq_count: number
}

export interface SyncPatientResponse {
  success: boolean
  patient_id: string
  rebuilt_mongodb: boolean
  regenerated_qdrant: boolean
  summary_version: number
  latency_ms: number
}

export interface SyncRebuildResponse {
  success: boolean
  triggered_count: number
  patient_ids: string[]
}

export interface SyncStatisticsResponse {
  sync_count: number
  failures: number
  retries: number
  dead_letters: number
  avg_latency_ms: number
  rebuilt_summaries: number
  vectors_regenerated: number
  vectors_skipped: number
}

export interface RagHealthSubsystem {
  status: string
  latency_ms?: number
  latency?: number
  reachable?: boolean
  error?: string
  provider?: string
  model?: string
  dimensions?: number
}

export interface RagHealthResponse {
  status: string
  groq: RagHealthSubsystem
  embedding: RagHealthSubsystem
  qdrant: RagHealthSubsystem
}

export interface RagStatisticsResponse {
  health_status: string
  caches: {
    query_hits: number
    query_misses: number
    query_hit_ratio: number
    embedding_hits: number
    embedding_misses: number
    embedding_hit_ratio: number
    retrieval_hits: number
    retrieval_misses: number
    retrieval_hit_ratio: number
    context_hits: number
    context_misses: number
    context_hit_ratio: number
    total_hits: number
    total_misses: number
    total_hit_ratio: number
  }
  embeddings: {
    embeddings_generated: number
    avg_latency_ms: number
    failed_embeddings: number
    avg_batch_size: number
    duplicate_chunks_skipped: number
  }
  retrieval: {
    searches_executed: number
    failed_searches: number
    avg_latency_ms: number
    avg_score: number
    duplicate_chunks_removed: number
    timeout_count: number
  }
  assembly: {
    assemblies_executed: number
    failed_assemblies: number
    avg_latency_ms: number
    avg_compression_ratio: number
    avg_tokens_assembled: number
    total_original_chunks: number
    total_removed_chunks: number
    section_counts: Record<string, number>
  }
  agent: {
    requests: number
    failures: number
    cache_hits: number
    cache_misses: number
    cache_hit_ratio: number
    avg_retrieval_latency_ms: number
    avg_ranking_latency_ms: number
    avg_context_latency_ms: number
    avg_latency_ms: number
    intent_counts: Record<string, number>
    collection_usage: Record<string, number>
  }
  orchestrator: {
    requests: number
    failures: number
    avg_latency_ms: number
    avg_llm_latency_ms: number
    avg_embedding_latency_ms: number
    avg_context_latency_ms: number
    avg_tokens: number
    total_cost: number
    model_usage: Record<string, number>
    success_rate: number
  }
  overall: {
    success_rate: number
    total_queries: number
    avg_query_latency_ms: number
    estimated_llm_cost_usd: number
  }
}

export interface RagBenchmarkCategory {
  intent: string
  avg_latency_ms: number
  avg_precision: number
  avg_recall: number
  avg_citation_quality: number
  query_details: {
    query: string
    latency_ms: number
    precision: number
    recall: number
    citation_quality: number
    duplicate_rate: number
    context_utilization: number
  }[]
}

export interface RagBenchmarkResponse {
  timestamp: string
  total_queries_run: number
  total_latency_ms: number
  avg_latency_per_query_ms: number
  avg_precision: number
  avg_recall: number
  avg_citation_quality: number
  avg_duplicate_rate: number
  avg_context_utilization: number
  categories: Record<string, RagBenchmarkCategory>
}

export interface RagEvaluateResponse {
  query: string
  patient_id?: string
  timestamp: string
  metrics: {
    precision: number
    recall: number
    latency_ms: number
    citation_quality: number
    chunk_relevance: number
    duplicate_rate: number
    context_utilization: number
  }
  parameters: {
    collections: string[]
    top_k: number
    score_threshold: number
    token_budget: number
  }
  retrieval_summary: {
    hits_count: number
    chunks_found: number
    duplicates_removed: number
    assembled_sections: string[]
  }
}

export interface GraphHealthResponse {
  graph_compiled: boolean
  graph_version: string
  registered_nodes: string[]
  registered_transitions: {
    source: string
    target?: string
    type: string
    mapping: Record<string, string>
  }[]
  active_executions: number
}

export interface GraphNodesResponse {
  nodes: string[]
}

export interface GraphTestRunRequest {
  query?: string
  patient_id?: string
  debug_mode?: boolean
  metadata?: Record<string, any>
}

export interface GraphTestRunResponse {
  trace: string[]
  timings: Record<string, number>
  execution_metadata: Record<string, any>
  state: Record<string, any>
}

export interface GraphStatisticsResponse {
  total_executions: number
  successful_executions: number
  failed_executions: number
  avg_latency: number
  timeout_count: number
  cancelled_count: number
  active_executions: number
  graph_version: string
  node_execution_count: Record<string, number>
  transition_count: Record<string, number>
}

export interface RouterIntentsResponse {
  supported_intents: string[]
  registered_agents: Record<string, string>
  routing_rules: {
    ROUTER_CONFIDENCE_HIGH: number
    ROUTER_CONFIDENCE_MEDIUM: number
    ROUTER_ENABLE_REGEX: boolean
    ROUTER_ENABLE_KEYWORDS: boolean
    ROUTER_DEBUG: boolean
  }
}

export interface RouterClassifyRequest {
  query: string
}

export interface RouterClassifyResponse {
  detected_intent: string
  confidence: number
  matched_rules: string[]
  selected_agent: string
}

export interface RouterTestRequest {
  query: string
  patient_id?: string
  debug_mode?: boolean
  metadata?: Record<string, any>
}

export interface RouterTestResponse {
  graph_trace: string[]
  routing_trace: string[]
  detected_intent: string
  selected_agent: string
  confidence: number
  latency_ms: number
}

export interface RouterStatisticsResponse {
  total_routed_requests: number
  average_routing_latency_ms: number
  confidence_distribution: Record<string, number>
  intent_distribution: Record<string, number>
  unknown_queries_count: number
  unknown_percentage: number
  fallback_count: number
  fallback_percentage: number
  routing_failures_count: number
}

export interface MedicalKnowledgeAgentResponse {
  answer: string
  citations: Record<string, any>[]
  confidence: number
  sources: string[]
  metadata: Record<string, any>
  usage: Record<string, number>
}

export interface SymptomAgentResponse {
  summary: string
  possible_causes: string[]
  red_flags: string[]
  recommended_action: string
  emergency: boolean
  citations: Record<string, any>[]
  metadata: Record<string, any>
  usage: Record<string, number>
}

export interface MemoryAgentResponse {
  memory_summary: string
  conversation_history: Record<string, any>[]
  patient_summary: string
  relevant_context: Record<string, any>[]
  metadata: Record<string, any>
}

export interface ReportAnalysisAgentResponse {
  summary: string
  key_findings: string[]
  abnormal_values: Record<string, any>[]
  trend_analysis: string[]
  recommendations: string[]
  citations: Record<string, any>[]
  metadata: Record<string, any>
  usage: Record<string, number>
}

export interface DrugInteractionAgentResponse {
  interaction_found: boolean
  severity: string
  interaction_summary: string
  warnings: string[]
  alternatives: string[]
  citations: Record<string, any>[]
  metadata: Record<string, any>
  usage: Record<string, number>
}

export interface DoctorRecommendationAgentResponse {
  recommended_doctors: Record<string, any>[]
  reasoning: string
  matching_specialization: string
  confidence: number
  metadata: Record<string, any>
  usage: Record<string, number>
}

export interface ReminderAgentResponse {
  status: string
  action: string
  message: string
  created_reminder?: Record<string, any>
  updated_reminder?: Record<string, any>
  deleted_id?: string
  warnings: string[]
  safety_check_details?: Record<string, any>
  usage: Record<string, number>
  metadata: Record<string, any>
}

export interface AppointmentAgentResponse {
  status: string
  action: string
  message: string
  search_results?: Record<string, any>[]
  slots?: Record<string, any>[]
  appointment?: Record<string, any>
  rescheduled_appointment?: Record<string, any>
  cancelled_id?: string
  reasoning?: string
  usage: Record<string, number>
  metadata: Record<string, any>
}

export interface AIExecuteRequest {
  query: string
  patient_id?: string
  session_id?: string
  conversation_id?: string
  debug_mode?: boolean
  metadata?: Record<string, any>
}

export interface StandardResponseContract {
  success: boolean
  agent?: string
  intent?: string
  response?: string
  citations: Record<string, any>[]
  metadata: Record<string, any>
  usage: Record<string, number>
  execution_trace: string[]
  execution_time: number
  cost: number
  warnings: string[]
}

export interface OrchestratorStatisticsResponse {
  total_executions: number
  intent_distribution: Record<string, number>
  agent_usage: Record<string, number>
  average_latency_ms: number
  total_token_usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  total_costs: number
  failures: number
  retries: number
  cache_hit_rate: number
  retrieval_metrics: Record<string, any>
}

export interface DrugMasterModel {
  drug_name: string
  normalized_name: string
  aliases: string[]
  source_dataset: string
}

export interface DrugLookupResponse {
  exists: boolean
  matched_drug: DrugMasterModel | null
  normalized_name: string
  lookup_source: string
  confidence: number
  latency_ms: number
}

export interface DrugNormalizeResponse {
  normalized_name: string
}

export interface DrugTelemetryResponse {
  total_lookups: number
  cache_hits: number
  cache_misses: number
  cache_hit_ratio: number
  avg_latency_ms: number
  unknown_drug_count: number
  normalization_count: number
}





