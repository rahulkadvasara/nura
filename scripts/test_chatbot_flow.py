"""
Nura Chatbot Flow Verification Script
Tests intent classification, routing decisions, LangGraph engine execution, and orchestrator contracts across 10 query scenarios.
"""

import sys
import os
import asyncio
import logging

# Ensure backend path is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_chatbot_flow")


TEST_CASES = [
    {
        "name": "1. Greeting Query",
        "query": "Hello Nura, good morning!",
        "expected_intent": "GREETING",
        "expected_agent": "GreetingAgent"
    },
    {
        "name": "2. General Chat Query",
        "query": "Who are you and what can you do?",
        "expected_intent": "GENERAL_CHAT",
        "expected_agent": "MedicalKnowledgeAgent"
    },
    {
        "name": "3. Medical Question Query",
        "query": "What are the main causes and symptoms of hypertension disease?",
        "expected_intent": "MEDICAL_QUESTION",
        "expected_agent": "MedicalKnowledgeAgent"
    },
    {
        "name": "4. Symptom Analysis Query",
        "query": "I have a severe headache, high fever, and nausea for 2 days",
        "expected_intent": "SYMPTOM_ANALYSIS",
        "expected_agent": "SymptomAgent"
    },
    {
        "name": "5. Report Analysis Query",
        "query": "Please review my cbc lab report results and cholesterol levels",
        "expected_intent": "REPORT_ANALYSIS",
        "expected_agent": "ReportAnalysisAgent"
    },
    {
        "name": "6. Drug Interaction Query",
        "query": "Can I take paracetamol and ibuprofen together? What is the side effect?",
        "expected_intent": "DRUG_INTERACTION",
        "expected_agent": "DrugInteractionAgent"
    },
    {
        "name": "7. Doctor Recommendation Query",
        "query": "Can you recommend a cardiologist specialist doctor near me?",
        "expected_intent": "DOCTOR_RECOMMENDATION",
        "expected_agent": "DoctorRecommendationAgent"
    },
    {
        "name": "8. Reminder Setup Query",
        "query": "Remind me to take my daily blood pressure pill at 8 AM",
        "expected_intent": "REMINDER",
        "expected_agent": "ReminderAgent"
    },
    {
        "name": "9. Appointment Booking Query",
        "query": "I want to book an appointment with a doctor for consultation",
        "expected_intent": "APPOINTMENT",
        "expected_agent": "AppointmentAgent"
    },
    {
        "name": "10. Conversation Recall Query",
        "query": "Do you remember what we discussed in our last conversation history?",
        "expected_intent": "CONVERSATION_RECALL",
        "expected_agent": "MemoryAgent"
    }
]


async def run_verification():
    logger.info("==================================================")
    logger.info("STARTING NURA CHATBOT VERIFICATION TEST SUITE")
    logger.info("==================================================")

    from app.agents.router.intent_classifier import IntentClassifier
    from app.agents.router.router_agent import RouterAgent
    from app.services.intent_detection_service import get_intent_detection_service
    from app.graph.engine import get_graph_engine
    
    classifier = IntentClassifier()
    router = RouterAgent()
    intent_service = get_intent_detection_service()
    engine = get_graph_engine()

    # Pre-warm retrieval agent to avoid cold-start timeouts
    try:
        from app.core.dependencies import get_retrieval_agent
        await get_retrieval_agent().run("warmup query", None)
    except Exception as e:
        logger.warning(f"Retrieval pre-warm skipped: {e}")

    passed_count = 0
    failed_count = 0

    for test in TEST_CASES:
        logger.info(f"\n--- Running Test: {test['name']} ---")
        query = test["query"]
        logger.info(f"Query: '{query}'")

        # 1. Test Classifier
        class_res = classifier.classify(query)
        logger.info(f"Classifier Intent: {class_res.intent} (Confidence: {class_res.confidence})")

        # 2. Test Router Decision
        decision = await router.run_routing(query)
        logger.info(f"Router Selected Agent: {decision.selected_agent} (Detected Intent: {decision.detected_intent})")

        # 3. Test IntentDetectionService
        service_intent = intent_service.detect_intent(query)
        logger.info(f"IntentDetectionService Detected: {service_intent}")

        # 4. Test LangGraph Execution Trace Simulation
        state_dict = {
            "request_id": f"test-{test['expected_intent']}",
            "session_id": "test-session-123",
            "conversation_id": "test-conv-123",
            "patient_id": "test-patient-123",
            "query": query,
            "metadata": {}
        }

        updated_state = await engine.execute_async(state_dict)
        trace = updated_state.get("execution_trace", [])
        final_agent = updated_state.get("selected_agent")
        final_intent = updated_state.get("detected_intent")
        response_preview = (updated_state.get("response") or "")[:100]

        logger.info(f"Graph Trace: {' -> '.join(trace)}")
        logger.info(f"Graph Final Agent: {final_agent}, Intent: {final_intent}")
        logger.info(f"Response Preview: '{response_preview}...'")

        # Assertions
        intent_match = decision.detected_intent == test["expected_intent"]
        agent_match = decision.selected_agent == test["expected_agent"]
        trace_contains_agent = test["expected_agent"] in trace

        if intent_match and agent_match and trace_contains_agent:
            logger.info(f"✅ PASSED: {test['name']}")
            passed_count += 1
        else:
            logger.error(f"❌ FAILED: {test['name']}")
            logger.error(f"   Expected Intent: {test['expected_intent']}, Got: {decision.detected_intent}")
            logger.error(f"   Expected Agent: {test['expected_agent']}, Got: {decision.selected_agent}")
            failed_count += 1

    logger.info("\n==================================================")
    logger.info(f"VERIFICATION SUMMARY: Passed {passed_count}/{len(TEST_CASES)}, Failed {failed_count}/{len(TEST_CASES)}")
    logger.info("==================================================")

    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_verification())
