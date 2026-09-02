import sys
import os
import asyncio
import logging

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

logging.basicConfig(level=logging.INFO)

async def main():
    print("\n--- 1. Testing Greeting Agent (Instant Default Greeting) ---")
    from app.agents.core.greeting_agent import GreetingAgent
    from app.agents.base.context import AgentContext
    
    greeting_agent = GreetingAgent()
    ctx = AgentContext(patient_id="6a3784b31466c381d1cb2179")
    res = await greeting_agent.execute("hello", ctx)
    print("Greeting Output:", res.greeting)
    print("Groq Latency (ms):", res.metadata.get("groq_latency_ms"))
    assert res.metadata.get("groq_latency_ms") == 0.0, "Expected 0ms LLM latency for Greeting"

    print("\n--- 2. Testing Unknown Agent (Instant Default Response) ---")
    from app.graph.nodes import UnknownAgentNode
    from app.graph.state import GraphState
    
    unknown_node = UnknownAgentNode()
    state = GraphState(query="xyz123")
    res_unknown = await unknown_node(state)
    print("Unknown Agent Output:\n", res_unknown["response"])
    assert "Symptom Triage" in res_unknown["response"]

    print("\n--- 3. Testing Symptom Agent (Risk Level & Doctor-like Assessment) ---")
    from app.agents.core.symptom_agent import SymptomAgent
    from app.core.dependencies import get_retrieval_agent, get_patient_context_service, get_ai_service
    
    symptom_agent = SymptomAgent(
        retrieval_agent=get_retrieval_agent(),
        patient_context_service=get_patient_context_service(),
        ai_service=get_ai_service()
    )
    symptom_res = await symptom_agent.execute("I have fever and severe cough for 3 days", ctx)
    print("Risk Level:", symptom_res.risk_level)
    print("Summary Output:\n", symptom_res.summary)
    assert symptom_res.risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert "Clinical Assessment" in symptom_res.summary

    print("\n--- 4. Testing Memory Agent (Recall from Past Patient Records) ---")
    from app.agents.core.memory_agent import MemoryAgent
    from app.core.dependencies import get_patient_memory_repository, get_chat_message_repository, get_retrieval_service, get_memory_sync_service
    
    memory_agent = MemoryAgent(
        patient_memory_repository=get_patient_memory_repository(),
        chat_message_repository=get_chat_message_repository(),
        retrieval_service=get_retrieval_service(),
        memory_sync_service=get_memory_sync_service(),
        patient_context_service=get_patient_context_service(),
        ai_service=get_ai_service()
    )
    mem_res = await memory_agent.execute("what appointments or reports do I have?", ctx)
    print("Memory Agent Summary:\n", mem_res.memory_summary)

    print("\n✅ ALL FEATURE VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
