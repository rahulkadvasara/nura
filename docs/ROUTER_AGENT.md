# Router Agent Architecture

The Router Agent is the production-grade entrypoint for all AI queries in the Nura Healthcare Platform. It deterministically classifies query intents and selects the appropriate downstream agent for execution without invoking LLMs, ensuring near-instant execution and low overhead.

---

## 1. Intent Classification

Queries are classified into one of 11 supported intents:
- `GREETING`: Welcome exchanges.
- `GENERAL_CHAT`: General chit-chat.
- `MEDICAL_QUESTION`: Health inquiries.
- `SYMPTOM_ANALYSIS`: Symptom checking.
- `REPORT_ANALYSIS`: Lab tests interpretation.
- `DRUG_INTERACTION`: Medications side-effects/clashes.
- `DOCTOR_RECOMMENDATION`: Suggested medical specialists.
- `REMINDER`: Task and medication alarms.
- `APPOINTMENT`: Medical consultations booking.
- `CONVERSATION_RECALL`: Longitudinal patient memory checks.
- `UNKNOWN`: Catch-all for unmapped or empty inputs.

### Scoring Methodology
Classification runs dynamically utilizing weighted rules matching:
- **Keyword Matches (Weight: `+2` per match)**: Evaluates query words using exact regex word boundaries (`\bkeyword\b`) to prevent partial substring overlaps (e.g. matching "rx" in "extra").
- **Regex Matches (Weight: `+5` per match)**: Evaluates query strings against structured pattern regular expressions.

---

## 2. Confidence Tier Evaluation

The classifier normalizes raw scores to determine a final confidence probability between `0.0` and `1.0`:
$$\text{Confidence} = \frac{\text{winning\_score}}{\sum \text{scores}} \times \frac{\text{winning\_score}}{\text{winning\_score} + 3.0}$$

This calculates a distinction ratio representing how clearly the winning intent stands out compared to other candidate intents, combined with a strength factor that adjusts confidence downward for single keyword matches.

Confidence values are classified into three tiers:
- **HIGH** (Confidence $\ge$ `ROUTER_CONFIDENCE_HIGH`): Immediate routing to the registered downstream agent.
- **MEDIUM** (Confidence $\ge$ `ROUTER_CONFIDENCE_MEDIUM`): Routes to the registered downstream agent.
- **LOW** (Confidence < `ROUTER_CONFIDENCE_MEDIUM`): Routes safely to `UnknownAgent`.

---

## 3. Fallback and Ambiguity Handling

The `FallbackManager` intercepts execution cases:
- **Unmatched Queries**: Returns `UnknownAgent` if all intent scores are 0.
- **Ambiguous Queries**: If the two highest candidate intents share identical scores, the query is marked as ambiguous and routes to `UnknownAgent`.
- **Empty Prompts / Errors**: Returns `UnknownAgent` with `0.0` confidence to ensure no unhandled exceptions fail the execution pipeline.

---

## 4. Extension Guide

To register a new downstream agent dynamically:
1. Call `get_intent_registry()`:
   ```python
   from app.agents.router import get_intent_registry
   registry = get_intent_registry()
   ```
2. Register the intent name mapped to the target agent:
   ```python
   registry.register_intent("NEW_INTENT", "NewDownstreamAgent")
   ```
   *Note: This will raise a `ValueError` if the intent name is already mapped.*
