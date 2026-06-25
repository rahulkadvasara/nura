# Nura - Agent Design Document

## 1. Purpose

This document defines the AI architecture of Nura.

It describes:

* Agent responsibilities
* Inputs
* Outputs
* Tools
* Dependencies
* LangGraph orchestration

The goal is to ensure all AI components remain modular, observable, and scalable.

---

# 2. AI Architecture Overview

Nura uses a Retrieval-Augmented Multi-Agent Architecture.

Workflow:

```text
User Query
↓
Router Agent
↓
Retrieval Agent
↓
Patient Context Builder
↓
Specialized Agent
↓
Memory Agent
↓
Response
```

---

# 3. Shared LangGraph State

```python
{
    "user_id": str,
    "query": str,
    "intent": str,
    "retrieved_context": list,
    "patient_context": dict,
    "selected_agent": str,
    "response": str,
    "metadata": dict
}
```

---

# 4. Router Agent

## Purpose

Determine user intent and select the appropriate specialized agent.

---

### Inputs

```text
User Query
Conversation History
```

---

### Outputs

```text
Intent
Target Agent
```

---

### Supported Intents

```text
symptom_analysis

medical_question

report_analysis

drug_interaction

doctor_recommendation

reminder_management

appointment_management
```

---

### Dependencies

```text
Groq
```

---

# 5. Retrieval Agent

## Purpose

Retrieve relevant context from vector databases and application data.

---

### Inputs

```text
Query
User ID
Intent
```

---

### Outputs

```text
Retrieved Context
```

---

### Sources

Qdrant:

```text
patient_reports
chat_memory
medical_knowledge
drug_knowledge
doctor_knowledge
```

MongoDB:

```text
patient_memory
appointments
consultations
prescriptions
reminders
doctor_profiles
```

---

### Dependencies

```text
Qdrant
MongoDB
Embedding Service
```

---

# 6. Patient Context Builder

## Purpose

Build a unified healthcare context for the user.

This is not an AI agent.

It performs aggregation only.

---

### Sources

Priority order:

1. patient_memory
2. Recent consultations
3. Recent prescriptions
4. Relevant reports
5. Relevant semantic memories
6. User profile
7. Current conversation

The builder should intelligently trim context to remain within token limits.

---

### Output

```json
{
  "recent_reports": [],
  "active_medications": [],
  "upcoming_appointments": [],
  "recent_consultations": [],
  "health_insights": []
}
```

---

# 7. Symptom Analysis Agent

## Purpose

Analyze symptoms and provide healthcare guidance.

---

### Inputs

```text
Symptoms
Retrieved Context
Patient Context
```

---

### Outputs

```text
Risk Level
Possible Causes
Recommendations
Suggested Specialty
```

---

### Risk Levels

```text
Low
Medium
High
Emergency
```

---

### Dependencies

```text
Groq
Medical Knowledge
```

---

# 8. Medical Knowledge Agent

## Purpose

Answer healthcare-related questions.

---

### Inputs

```text
Question
Retrieved Context
```

---

### Outputs

```text
Educational Medical Response
```

---

### Constraints

```text
No diagnosis
No prescriptions
No treatment guarantees
```

---

### Dependencies

```text
Groq
Medical Knowledge Collection
```

---

# 9. Report Analysis Agent

## Purpose

Analyze uploaded medical reports.

---

### Inputs

```text
Report Text
Structured Data
Entities
```

---

### Outputs

```text
Summary
Risk Level
Recommendations
Health Insights
```

---

### Risk Levels

```text
Low
Medium
High
```

---

### Dependencies

```text
Groq
Medical Knowledge
Patient Reports
```

---

# 10. Drug Interaction Agent

## Purpose

Validate medication safety.

---

### Inputs

```text
Drug List
Medication Query
```

---

### Workflow

```text
RxNorm Normalization
↓
Interaction Retrieval
↓
Risk Classification
↓
Recommendation
```

---

### Outputs

```text
Interaction Results
Risk Level
Safety Guidance
```

---

### Risk Levels

```text
Low
Medium
High
```

---

### Dependencies

```text
Drug Interaction Dataset
Qdrant Drug Knowledge Collection
```

---

# 11. Doctor Recommendation Agent

## Purpose

Recommend relevant doctors.

---

### Inputs

```text
Symptoms
Specialty Requirements
Location Filters
```

---

### Outputs

```text
Recommended Doctors
Ranking Scores
Reasoning
```

---

### Dependencies

```text
Doctor Profiles
Doctor Knowledge Collection
```

---

# 12. Reminder Agent

## Purpose

Validate and create reminders.

---

### Inputs

```text
Reminder Request
Medication Information
```

---

### Outputs

```text
Reminder Validation
Reminder Recommendation
```

---

### Dependencies

```text
Drug Interaction Agent
Reminder Service
```

---

# 13. Appointment Agent

## Purpose

Support appointment workflows.

---

### Inputs

```text
Doctor Selection
Appointment Request
Availability Data
```

---

### Outputs

```text
Appointment Guidance
Availability Suggestions
```

---

### Dependencies

```text
Appointments
Doctor Availability
```

---

# 14. Memory Agent

## Purpose

Maintain long-term conversation memory.
Raw conversations remain in MongoDB. Qdrant stores only condensed semantic memories.

Strategy:
MongoDB -> Conversation Summarizer -> Semantic Memory -> chat_memory (Qdrant)

---

### Inputs

```text
User Query
Agent Response
```

---

### Outputs

```text
Stored Memory
Embedding
Metadata
```

---

### Storage

Qdrant:

```text
chat_memory
```

MongoDB:

```text
chat_sessions
chat_messages
```

---

# 15. Agent Observability

All agent executions must generate logs.

Collection:

```text
agent_logs
```

Schema:

```json
{
  "agent_name": "string",
  "user_id": "string",
  "query": "string",
  "latency_ms": 0,
  "status": "success",
  "created_at": "datetime"
}
```

---

# 16. Safety Requirements

All AI responses must:

* Avoid medical diagnosis claims
* Avoid treatment guarantees
* Recommend professional consultation for high-risk situations
* Flag emergency symptoms immediately

---

# 17. Future Agents

Potential future additions:

```text
Insurance Agent

Telemedicine Agent

Health Forecasting Agent

Voice Assistant Agent

Wearable Analytics Agent
```

---

# 18. Definition of Done

AI architecture is considered complete when:

* Router correctly classifies intent
* Retrieval returns relevant context
* Patient Context Builder aggregates healthcare data
* Specialized agents produce grounded responses
* Memory persists successfully
* Agent logs are generated
* Safety rules are enforced

```
```
