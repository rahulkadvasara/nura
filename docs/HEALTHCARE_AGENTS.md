# Nura Healthcare Platform - Healthcare Intelligence Agents

This document describes the design, implementation, safety constraints, and workflows of the three production-grade healthcare intelligence agents introduced in Phase 10 – Sprint 4: **ReportAnalysisAgent**, **DrugInteractionAgent**, and **DoctorRecommendationAgent**.

---

## 1. System Architecture

The healthcare agents are encapsulated within the package `backend/app/agents/healthcare/` and inherit from the standard `BaseAgent` framework. They plug directly into:
- **Router Agent & Intent Registry**: The Router classifies the clinical intent (e.g. `REPORT_ANALYSIS`) and routes the incoming query to the corresponding agent.
- **LangGraph Workflow**: Dispatched dynamically using conditional transitions from the Router node to the individual agent executor node, which then terminates at the `Finish` node.
- **Retrieval Pipeline**: Querying Qdrant database collections (`patient_reports`, `drug_knowledge`, `doctor_knowledge`) for grounding context.
- **Patient Context Builder**: Assembling patient-specific details from MongoDB.
- **AI Telemetry System**: Accumulating metrics (executions, costs, latencies, tokens, citation count) separately for tracking inside the healthcare telemetry singleton.

---

## 2. Workflows and Pipelines

### A. Report Analysis Agent
- **Purpose**: Grounded medical report explanation.
- **Workflow**:
  1. Patient query ➔ RetrievalAgent queries the Qdrant `patient_reports` collection.
  2. Patient Context ➔ Patient details fetched from MongoDB via `PatientContextService`.
  3. Report Metadata ➔ List of recent patient reports queried from `ReportRepository` to check risk levels and upload dates.
  4. Prompt Builder ➔ Renders the report templates with metadata, patient profile, and retrieved report text chunks.
  5. Groq ➔ Generates explanation JSON.
  6. Response ➔ Deserialized into `ReportAnalysisAgentResponse`.

### B. Drug Interaction Agent
- **Purpose**: Verify safety conflicts.
- **Workflow**:
  1. Patient query ➔ RetrievalAgent queries Qdrant `drug_knowledge` and `patient_reports` collections.
  2. Patient Memory ➔ Retrieves active medications, chronic conditions, and allergy history from MongoDB `PatientMemoryRepository`.
  3. Prompt Builder ➔ Compiles medications list, allergies, and retrieved safety facts.
  4. Groq ➔ Performs interaction diagnostics and returns JSON.
  5. Safety Disclosures ➔ Asserts informational disclaimers and wraps results in `DrugInteractionAgentResponse` with severity risk badge.

### C. Doctor Recommendation Agent
- **Purpose**: Recommendation and ranking of suitable specialists.
- **Workflow**:
  1. Symptoms query ➔ RetrievalAgent semantic search over the `doctor_knowledge` collection in Qdrant.
  2. Availability Lookup ➔ Queries MongoDB `DoctorAvailabilityRepository` using matched doctor IDs for active slots.
  3. Patient Location ➔ Fetches patient city/address location context.
  4. Groq ➔ Ranks doctors matching specialization, hospital, languages, and experience.
  5. Response ➔ Deserialized into `DoctorRecommendationAgentResponse`.

---

## 3. Regulatory Safety Rules

To ensure clinical compliance, the agents enforce strict safety safeguards:
1. **Report Analysis Safety**:
   - Never modify or write medical report metrics.
   - All claims must be grounded in report text chunks with precise citations.
2. **Medication safety disclaimers**:
   - Always include the warning: *"This drug safety check is for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your physician before starting, stopping, or changing any medication."*
   - Never prescribe medication or recommend dosage adjustments.
3. **Doctor Match limits**:
   - Prohibit querying the doctor profiles collection in MongoDB directly for search/match queries (must run semantic vector search over Qdrant first, except for availability lookup).

---

## 4. Response Schemas

### `ReportAnalysisAgentResponse`
- `summary` (string): Clear, patient-friendly findings summary.
- `key_findings` (string[]): Key diagnostic findings list.
- `abnormal_values` (object[]): List of abnormal metrics found (`metric`, `value`, `normal_range`, `status`).
- `trend_analysis` (string[]): Trends comparing past report values.
- `recommendations` (string[]): Safe recommendations and next steps.
- `citations` (object[]): Chunks references used.

### `DrugInteractionAgentResponse`
- `interaction_found` (boolean): Safety conflicts flag.
- `severity` (string): Low, Medium, High, or Critical.
- `interaction_summary` (string): Safety warning summary text.
- `warnings` (string[]): Warnings list.
- `alternatives` (string[]): Suggested alternative treatments to discuss.

### `DoctorRecommendationAgentResponse`
- `recommended_doctors` (object[]): Ranked doctors profiles with active slots.
- `reasoning` (string): Selection reason narrative.
- `matching_specialization` (string): Target doctor specialization.
- `confidence` (float): Specialized matching score.

---

## 5. Extension Guide

To add a new healthcare agent (e.g. `AppointmentAgent`):
1. **Add Prompts**: Create template markdown files in `backend/app/prompts/system/` and `backend/app/prompts/templates/`. Register them in `PromptLoader.versions` inside `loader.py`.
2. **Implement Agent**: Create `appointment_agent.py` in `backend/app/agents/healthcare/` extending `BaseAgent`.
3. **DI Getter**: Add `get_appointment_agent()` in `dependencies.py`.
4. **Register Graph Node**: Declare `AppointmentAgentNode` in `nodes.py` and register it inside `get_graph_engine()` in `engine.py`.
5. **Route Intent**: Map the intent key in `IntentRegistry` defaults (in `intent_registry.py`).
