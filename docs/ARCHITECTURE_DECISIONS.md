# Architecture Decisions

## ADR-001

Decision:
Use MongoDB Atlas as primary database.

Reason:
Flexible healthcare schema and rapid development.

---

## ADR-002

Decision:
Use Qdrant for vector search.

Reason:
Fast similarity search and RAG support.

---

## ADR-003

Decision:
Use LangGraph instead of CrewAI.

Reason:
Better workflow orchestration and state management.

---

## ADR-004

Decision:
Use Patient Context Builder between Retrieval and Specialized Agents.

Reason:
Provide consistent healthcare context to all agents.

---

## ADR-005

Decision:
Use Escrow Payment Model.

Reason:
Support automatic refunds when appointments are rejected.

---

## ADR-006

Decision:
Store structured report data in addition to summaries.

Reason:
Supports future analytics and trend analysis.