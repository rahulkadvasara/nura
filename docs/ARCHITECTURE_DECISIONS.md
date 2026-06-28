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

---

## ADR-007

Decision:
Use a single ADMIN role without a Super Admin role. All admins share identical permissions.

Reason:
Simplifies permission architecture and minimizes overhead for the initial administrative lifecycle while providing complete operational control.

---

## ADR-008

Decision:
Automatically bootstrap the first admin account using environment variables on system startup if no admin exists.

Reason:
Ensures the platform is immediately operational on fresh deployments and provides a secure, configuration-driven seeding mechanism.

---

## ADR-009

Decision:
Enforce backend rules preventing the disabling or deletion of the last remaining administrator account.

Reason:
Guarantees administrative access is never permanently lost and prevents accidental lockout situations.

---

## ADR-010

Decision:
Use `patient_memory` MongoDB collection as the primary source of truth for longitudinal patient context. Qdrant stores only condensed semantic memories and domain knowledge.

Reason:
Ensures transactional integrity, provides low-latency reads for Doctor Dashboards without invoking the LLM, and creates a clean separation of operational records from vector embeddings.

---

## ADR-011

Decision:
Simplify Drug Safety Architecture by using MongoDB (`drug_master`, `drug_interactions`) as the single source of truth for drug data, removing the `drug_knowledge` Qdrant collection, and restricting Groq's role to generating explanations without determining interaction severity.

Reason:
MongoDB provides deterministic drug interactions and normalizations. The `drug_knowledge` Qdrant collection introduces duplicate storage and unnecessary complexity, while semantic search is not reliable enough for determining clinical interactions.