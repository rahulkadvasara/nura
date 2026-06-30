# Chat Infrastructure & Session Management Architecture

This document outlines the database schemas, REST API contracts, lifecycle operations, and the future integration plans for the Nura Conversational AI Platform.

---

## 1. Database Schema

Nura uses MongoDB to store and manage persistent chat conversations and message history. The platform implements two primary collections.

### Collection: `chat_sessions`
Represents a unique conversation channel initiated by a patient.

```json
{
  "_id": "ObjectId",
  "patient_id": "string (User ID)",
  "title": "string",
  "description": "string (optional)",
  "status": "ACTIVE | ARCHIVED | DELETED",
  "session_type": "string (e.g., ai_chat)",
  "active": "boolean",
  "last_message_at": "ISODate",
  "message_count": "int",
  "total_tokens": "int",
  "total_cost": "double",
  "last_agent_used": "string (optional)",
  "pinned": "boolean",
  "archived": "boolean",
  "metadata": "object",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### Collection: `chat_messages`
Represents individual messages exchanged within a chat session.

```json
{
  "_id": "ObjectId",
  "session_id": "string (Session ID)",
  "patient_id": "string (Patient User ID)",
  "role": "USER | ASSISTANT | SYSTEM",
  "content": "string (message body)",
  "citations": [
    {
      "source": "string",
      "collection": "string",
      "document_id": "string",
      "page_number": "int",
      "score": "double"
    }
  ],
  "attachments": "array",
  "token_usage": {
    "prompt_tokens": "int",
    "completion_tokens": "int",
    "total_tokens": "int"
  },
  "latency_ms": "int (optional)",
  "metadata": "object",
  "created_at": "ISODate",
  "edited_at": "ISODate (optional)",
  "deleted": "boolean"
}
```

---

## 2. REST APIs

All chat endpoints are exposed under `/api/v1/chat`.

### CRUD Session Operations

* **POST `/session`**
  * **Role**: `PATIENT` (must match `patient_id`)
  * **Payload**: `ChatSessionCreate` schema (patient_id, title, description, session_type)
  * **Response**: `SuccessResponse` with `ChatSessionResponse`

* **GET `/sessions`**
  * **Role**: `PATIENT`
  * **Query Parameters**: `limit` (default: 20), `skip` (default: 0), `include_archived` (default: true)
  * **Sorting**: Pinned sessions first, followed by newest based on `last_message_at` descending.
  * **Response**: `SuccessResponse` with an array of `ChatSessionResponse`

* **GET `/session/{session_id}`**
  * **Role**: `PATIENT`
  * **Response**: `SuccessResponse` with `ChatSessionResponse`

* **PATCH `/session/{session_id}`**
  * **Role**: `PATIENT`
  * **Payload**: `ChatSessionUpdate` schema (title, description, pinned, archived, status)
  * **Response**: `SuccessResponse` with updated `ChatSessionResponse`

* **DELETE `/session/{session_id}`**
  * **Role**: `PATIENT`
  * **Behavior**: Soft delete. Updates the session's status to `DELETED` and sets `active` to `false`.
  * **Response**: `SuccessResponse`

---

### Message & History Operations

* **POST `/message`**
  * **Role**: `PATIENT`
  * **Payload**: `ChatMessageCreate` schema (session_id, patient_id, role, content, citations, token_usage, latency_ms, metadata)
  * **Response**: `SuccessResponse` with `ChatMessageResponse`

* **GET `/messages/{session_id}`**
  * **Role**: `PATIENT`
  * **Query Parameters**: `limit` (default: 50), `skip` (default: 0)
  * **Behavior**: Returns non-deleted messages sorted chronologically ascending.
  * **Response**: `SuccessResponse` with `ChatHistoryResponse`

---

### Telemetry Operations

* **GET `/statistics`**
  * **Role**: `ADMIN`
  * **Behavior**: Returns global statistics across all chat sessions and messages.
  * **Response**: `SuccessResponse` with `ChatStatisticsResponse` containing:
    * `sessions_created`
    * `sessions_archived`
    * `sessions_deleted`
    * `messages_created`
    * `messages_edited`
    * `messages_deleted`
    * `average_messages_per_session`

---

## 3. Session Lifecycle State Machine

A chat session moves through several states during its active existence:

```mermaid
stateDiagram-v2
    [*] --> ACTIVE : POST /session
    ACTIVE --> PINNED : PATCH pinned=true
    PINNED --> ACTIVE : PATCH pinned=false
    ACTIVE --> ARCHIVED : PATCH archived=true
    ARCHIVED --> ACTIVE : PATCH archived=false
    ACTIVE --> DELETED : DELETE /session (soft-delete)
    ARCHIVED --> DELETED : DELETE /session (soft-delete)
    DELETED --> ACTIVE : PATCH status=ACTIVE (restore)
    DELETED --> [*]
```

---

## 4. Active AI execution Pipeline Architecture

The AI Chat Execution Pipeline links the persistent MongoDB chat storage to the LangGraph Multi-Agent Orchestrator. 

### Sequence Diagram of Chat Execution

```mermaid
sequenceDiagram
    autonumber
    actor Patient as Patient (UI)
    participant API as FastAPI Router
    participant ExecService as ChatExecutionService
    participant ContextBuilder as ContextBuilder
    participant Orchestrator as Multi-Agent Orchestrator
    participant Agents as Target Agent (e.g. Memory/Symptom)
    participant DB as MongoDB (Chat Collections)

    Patient->>API: POST /message/execute (session_id, query)
    API->>ExecService: execute_chat_message(...)
    ExecService->>DB: Save USER Message (content=query)
    ExecService->>ContextBuilder: build_conversation_context(...)
    ContextBuilder->>DB: Fetch last 20 messages (excluding deleted)
    DB-->>ContextBuilder: Raw message history documents
    ContextBuilder-->>ExecService: Formatted context list [{"role", "content"}]
    ExecService->>Orchestrator: execute(AIExecuteRequest) with context in metadata
    Orchestrator->>Agents: Intent router dispatch
    Agents-->>Orchestrator: AgentResponse (citations, tokens, latency, cost)
    Orchestrator-->>ExecService: StandardResponseContract
    ExecService->>DB: Save ASSISTANT Message (content, citations, tokens, latency)
    ExecService->>DB: Update Session costs (total_cost, last_agent_used)
    ExecService-->>API: ChatExecutionResponse
    API-->>Patient: 201 Created (assistant_message, citations, usage, cost)
```

---

## 5. Components Details

### 5.1 Context Builder
The `build_conversation_context` utility aggregates the temporal chat history:
* Retrieves the last `limit` messages from `chat_messages` (default limit of 20).
* Translates message schemas: `USER` → `user`, `ASSISTANT` → `assistant`, `SYSTEM` → `system`.
* Appends metadata descriptions at the top of the context window as a `system` instruction.

### 5.2 Error Handling & Resilience
In the event of an orchestrator crash or Groq API failure:
* The user's query remains persisted in the `chat_messages` collection, preserving conversation logs.
* No assistant reply document is created.
* An error response is returned to the user interface, prompting them to retry.

### 5.3 Telemetry Flow
Admin statistics are aggregated on-the-fly directly from MongoDB collections:
* **AI Requests**: Count of assistant messages.
* **Failures**: Real-time counter queried from the thread-safe `MultiAgentTelemetryTracker` singleton.
* **Latency**: Calculated using MongoDB `$avg` pipeline on `$latency_ms`.
* **Token Usage & Costs**: Summarized using MongoDB `$sum` operators on the nested tokens and cost properties.
* **Agent Distribution**: Formed using MongoDB `$group` on `metadata.agent`.

