"""
Nura - LangGraph Infrastructure Nodes
Infrastructure callables executing startup, initialization, router placeholder, and completion.
"""

import time
import uuid
from typing import Dict, Any
from app.graph.state import GraphState
from app.graph.constants import (
    START_NODE,
    INIT_STATE_NODE,
    ROUTER_AGENT_NODE,
    FINISH_NODE,
    INTENT_DETECTION_NODE,
    PATIENT_CONTEXT_BUILDER_NODE,
    RETRIEVAL_AGENT_NODE,
    RESPONSE_VALIDATION_NODE,
    MEMORY_UPDATE_NODE,
    TELEMETRY_NODE,
)


class StartNode:
    """Starting gateway node initiating graph execution log trace"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(START_NODE)
        return {
            "current_node": START_NODE,
            "previous_node": None,
            "execution_trace": trace
        }


class InitializeStateNode:
    """Prepares and validates base workflow state variables (request_id, timestamps, defaults)"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(INIT_STATE_NODE)
        
        updates: Dict[str, Any] = {
            "current_node": INIT_STATE_NODE,
            "previous_node": state.current_node,
            "execution_trace": trace
        }
        
        # Initialize default execution properties if missing
        if not state.request_id:
            updates["request_id"] = str(uuid.uuid4())
        if not state.session_id:
            updates["session_id"] = str(uuid.uuid4())
            
        # Log system status initialize
        meta = dict(state.metadata or {})
        meta["initialized_at"] = time.time()
        updates["metadata"] = meta
        
        return updates


class RouterAgentNode:
    """Executes Router Agent to classify user query intent and choose target agent"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_router_agent
        router_agent = get_router_agent()
        
        # Execute routing classification
        decision = await router_agent.run_routing(state.query or "")
        
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(ROUTER_AGENT_NODE)
        
        meta = dict(state.metadata or {})
        meta["routing_confidence"] = decision.confidence
        meta["matched_rules"] = decision.matched_rules
        
        return {
            "current_node": ROUTER_AGENT_NODE,
            "previous_node": state.current_node,
            "detected_intent": decision.detected_intent,
            "selected_agent": decision.selected_agent,
            "execution_trace": trace,
            "metadata": meta
        }


class FinishNode:
    """Terminal node wrapping up execution status, compiling latencies and finalizing responses"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(FINISH_NODE)
        
        updates: Dict[str, Any] = {
            "current_node": FINISH_NODE,
            "previous_node": state.current_node,
            "execution_trace": trace
        }
        
        # Calculate execution latency if start time is logged in metadata
        init_time = (state.metadata or {}).get("initialized_at")
        if init_time:
            latency = (time.time() - init_time) * 1000.0
            updates["execution_time"] = latency
            
        # Default mock completion response if none is set
        if not state.response:
            updates["response"] = "Mock execution completed successfully via graph infrastructure nodes."
            
        return updates


class MedicalKnowledgeAgentNode:
    """Executes MedicalKnowledgeAgent to answer medical questions using RAG"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_medical_knowledge_agent
        from app.agents.base.context import AgentContext
        
        agent = get_medical_knowledge_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("MedicalKnowledgeAgent")
        
        if not res.success:
            return {
                "current_node": "MedicalKnowledgeAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        
        return {
            "current_node": "MedicalKnowledgeAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": res.response.answer if hasattr(res.response, "answer") else str(res.response),
            "citations": getattr(res.response, "citations", []),
            "metadata": meta,
            "token_usage": getattr(res.response, "usage", {})
        }


class SymptomAgentNode:
    """Executes SymptomAgent to analyze user-reported symptoms"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_symptom_agent
        from app.agents.base.context import AgentContext
        
        agent = get_symptom_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("SymptomAgent")
        
        if not res.success:
            return {
                "current_node": "SymptomAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        symptom_data = res.response
        meta["symptom_analysis"] = symptom_data.model_dump() if hasattr(symptom_data, "model_dump") else symptom_data
        
        return {
            "current_node": "SymptomAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": symptom_data.summary if hasattr(symptom_data, "summary") else str(symptom_data),
            "citations": getattr(symptom_data, "citations", []),
            "metadata": meta,
            "token_usage": getattr(symptom_data, "usage", {})
        }


class MemoryAgentNode:
    """Executes MemoryAgent to retrieve and update longitudinal memory"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_memory_agent
        from app.agents.base.context import AgentContext
        
        agent = get_memory_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("MemoryAgent")
        
        if not res.success:
            return {
                "current_node": "MemoryAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        mem_data = res.response
        meta["memory_analysis"] = mem_data.model_dump() if hasattr(mem_data, "model_dump") else mem_data
        
        return {
            "current_node": "MemoryAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": mem_data.memory_summary if hasattr(mem_data, "memory_summary") else str(mem_data),
            "metadata": meta
        }


class UnknownAgentNode:
    """Fallback agent node handling unrecognized intents"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("UnknownAgent")
        return {
            "current_node": "UnknownAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": "I'm sorry, I could not classify your query's clinical intent. Please try rephrasing your symptoms or question."
        }


class ReportAnalysisAgentNode:
    """Executes ReportAnalysisAgent to explain findings from medical reports"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_report_analysis_agent
        from app.agents.base.context import AgentContext
        
        agent = get_report_analysis_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("ReportAnalysisAgent")
        
        if not res.success:
            return {
                "current_node": "ReportAnalysisAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        report_data = res.response
        meta["report_analysis"] = report_data.model_dump() if hasattr(report_data, "model_dump") else report_data
        
        return {
            "current_node": "ReportAnalysisAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": report_data.summary if hasattr(report_data, "summary") else str(report_data),
            "citations": getattr(report_data, "citations", []),
            "metadata": meta,
            "token_usage": getattr(report_data, "usage", {})
        }


class DrugInteractionAgentNode:
    """Executes DrugInteractionAgent to validate safety of medications"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_drug_interaction_agent
        from app.agents.base.context import AgentContext
        
        agent = get_drug_interaction_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("DrugInteractionAgent")
        
        if not res.success:
            return {
                "current_node": "DrugInteractionAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        drug_data = res.response
        meta["drug_interaction_analysis"] = drug_data.model_dump() if hasattr(drug_data, "model_dump") else drug_data
        
        return {
            "current_node": "DrugInteractionAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": drug_data.interaction_summary if hasattr(drug_data, "interaction_summary") else str(drug_data),
            "citations": getattr(drug_data, "citations", []),
            "metadata": meta,
            "token_usage": getattr(drug_data, "usage", {})
        }


class DoctorRecommendationAgentNode:
    """Executes DoctorRecommendationAgent to find suitable doctors"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_doctor_recommendation_agent
        from app.agents.base.context import AgentContext
        
        agent = get_doctor_recommendation_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("DoctorRecommendationAgent")
        
        if not res.success:
            return {
                "current_node": "DoctorRecommendationAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        doctor_data = res.response
        meta["doctor_recommendations_analysis"] = doctor_data.model_dump() if hasattr(doctor_data, "model_dump") else doctor_data
        return {
            "current_node": "DoctorRecommendationAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": doctor_data.reasoning if hasattr(doctor_data, "reasoning") else str(doctor_data),
            "metadata": meta,
            "token_usage": getattr(doctor_data, "usage", {})
        }


class ReminderAgentNode:
    """Executes ReminderAgent to create or manage patient reminders"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_reminder_agent
        from app.agents.base.context import AgentContext
        
        agent = get_reminder_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("ReminderAgent")
        
        if not res.success:
            return {
                "current_node": "ReminderAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        reminder_data = res.response
        meta["reminder_analysis"] = reminder_data.model_dump() if hasattr(reminder_data, "model_dump") else reminder_data
        
        return {
            "current_node": "ReminderAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": reminder_data.message if hasattr(reminder_data, "message") else str(reminder_data),
            "metadata": meta,
            "token_usage": getattr(reminder_data, "usage", {})
        }


class AppointmentAgentNode:
    """Executes AppointmentAgent to schedule, cancel or search appointments"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_appointment_agent
        from app.agents.base.context import AgentContext
        
        agent = get_appointment_agent()
        ctx = AgentContext(
            request_id=state.request_id,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            patient_id=state.patient_id,
            doctor_id=state.doctor_id,
            user_id=state.user_id,
            role=state.role,
            metadata=dict(state.metadata or {})
        )
        
        res = await agent.run(state.query, ctx)
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append("AppointmentAgent")
        
        if not res.success:
            return {
                "current_node": "AppointmentAgent",
                "previous_node": state.current_node,
                "execution_trace": trace,
                "error": res.message
            }
            
        meta = dict(state.metadata or {})
        meta.update(res.metadata or {})
        appointment_data = res.response
        meta["appointment_analysis"] = appointment_data.model_dump() if hasattr(appointment_data, "model_dump") else appointment_data
        
        return {
            "current_node": "AppointmentAgent",
            "previous_node": state.current_node,
            "execution_trace": trace,
            "response": appointment_data.message if hasattr(appointment_data, "message") else str(appointment_data),
            "metadata": meta,
            "token_usage": getattr(appointment_data, "usage", {})
        }


class IntentDetectionNode:
    """Verifies and logs the classified intent mapped during the routing stage"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(INTENT_DETECTION_NODE)
        
        # Ensure intent is logged in metadata
        meta = dict(state.metadata or {})
        meta["final_intent"] = state.detected_intent or "UNKNOWN"
        meta["final_agent"] = state.selected_agent or "UnknownAgent"
        
        return {
            "current_node": INTENT_DETECTION_NODE,
            "previous_node": state.current_node,
            "execution_trace": trace,
            "metadata": meta
        }


class PatientContextBuilderNode:
    """Compiles MongoDB clinical longitudinal record metrics summary context"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(PATIENT_CONTEXT_BUILDER_NODE)
        
        patient_context_str = "No patient context provided."
        meta = dict(state.metadata or {})
        
        if state.patient_id:
            try:
                from app.core.dependencies import get_patient_context_service
                context_service = get_patient_context_service()
                context_res = await context_service.assemble_context(state.patient_id)
                
                parts = []
                if context_res.patient_profile:
                    parts.append(f"Name: {context_res.patient_profile.get('full_name')}")
                if context_res.medical_summary:
                    parts.append(f"Summary: {context_res.medical_summary}")
                if context_res.current_conditions:
                    parts.append(f"Conditions: {', '.join(context_res.current_conditions)}")
                if context_res.current_medications:
                    parts.append(f"Medications: {', '.join(context_res.current_medications)}")
                if context_res.medication_allergies:
                    parts.append(f"Allergies: {', '.join(context_res.medication_allergies)}")
                
                patient_context_str = "\n".join(parts) if parts else "No records available for this patient."
                meta["patient_context_sections"] = context_res.metadata.sections_returned
            except Exception as e:
                # Never crash the node, log and fall back gracefully
                patient_context_str = f"Error compiling patient context: {str(e)}"
                meta["patient_context_error"] = str(e)
                
        return {
            "current_node": PATIENT_CONTEXT_BUILDER_NODE,
            "previous_node": state.current_node,
            "patient_context": patient_context_str,
            "execution_trace": trace,
            "metadata": meta
        }


class RetrievalAgentNode:
    """Executes RetrievalAgent to pull relevant knowledge base vector chunks"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(RETRIEVAL_AGENT_NODE)
        
        retrieved_context_str = ""
        citations = []
        meta = dict(state.metadata or {})
        
        # Only perform retrieval if there is a search query
        if state.query:
            try:
                from app.core.dependencies import get_retrieval_agent
                from app.agents.base.context import AgentContext
                
                retrieval_agent = get_retrieval_agent()
                ctx = AgentContext(
                    request_id=state.request_id,
                    session_id=state.session_id,
                    conversation_id=state.conversation_id,
                    patient_id=state.patient_id,
                    doctor_id=state.doctor_id,
                    user_id=state.user_id,
                    role=state.role,
                    metadata=dict(state.metadata or {})
                )
                
                res = await retrieval_agent.run(state.query, ctx)
                if res.success and res.response:
                    retrieved_context_str = res.response.get("context", "")
                    retrieved_chunks = res.response.get("retrieved_chunks", [])
                    citations = [
                        {
                            "source": chunk.get("metadata", {}).get("source", "unknown"),
                            "text": chunk.get("text", ""),
                            "score": chunk.get("score", 0.0)
                        }
                        for chunk in retrieved_chunks
                    ]
                    meta["collections_used"] = res.response.get("collections_used", [])
            except Exception as e:
                retrieved_context_str = f"Partial retrieval failure: {str(e)}"
                meta["retrieval_error"] = str(e)
                
        return {
            "current_node": RETRIEVAL_AGENT_NODE,
            "previous_node": state.current_node,
            "retrieved_context": retrieved_context_str,
            "citations": citations,
            "execution_trace": trace,
            "metadata": meta
        }


class ResponseValidationNode:
    """Validates structural correctness of downstream responses and handles error recovery fallbacks"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(RESPONSE_VALIDATION_NODE)
        
        response_text = state.response
        error_msg = state.error
        meta = dict(state.metadata or {})
        
        # Error recovery/timeout fallbacks
        if error_msg:
            meta["validation_error"] = error_msg
            if not response_text:
                # Structure graceful recovery fallback error message
                response_text = f"An error occurred during workflow execution: {error_msg}. Please try rephrasing or contact support."
        elif not response_text:
            response_text = "Work completed, but no standard output was returned by the selected agent."
            
        return {
            "current_node": RESPONSE_VALIDATION_NODE,
            "previous_node": state.current_node,
            "response": response_text,
            "execution_trace": trace,
            "metadata": meta
        }


class MemoryUpdateNode:
    """Triggers Phase 9 Incremental Memory Synchronization Pipeline for write events"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(MEMORY_UPDATE_NODE)
        
        meta = dict(state.metadata or {})
        
        # Synchronization is triggered upon successful run of core/operations agents
        if state.patient_id and not state.error:
            trigger_agents = {
                "ReportAnalysisAgent",
                "ReminderAgent",
                "AppointmentAgent",
                "MedicalKnowledgeAgent",
                "SymptomAgent",
                "MemoryAgent"
            }
            if state.selected_agent in trigger_agents:
                try:
                    from app.core.dependencies import get_memory_sync_service
                    sync_service = get_memory_sync_service()
                    await sync_service.sync_patient(state.patient_id)
                    meta["memory_sync_triggered"] = True
                except Exception as e:
                    # Do not crash the graph on memory sync failure; log it in metadata
                    meta["memory_sync_error"] = str(e)
                    
        return {
            "current_node": MEMORY_UPDATE_NODE,
            "previous_node": state.current_node,
            "execution_trace": trace,
            "metadata": meta
        }


class TelemetryNode:
    """Aggregates latency, cost estimation, and token counts thread-safely"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(TELEMETRY_NODE)
        
        # Fetch cost and token estimations
        usage = dict(state.token_usage or {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        from app.utils.ai import estimate_cost
        cost = 0.0
        if state.metadata and "model" in state.metadata:
            cost = estimate_cost(state.metadata["model"], prompt_tokens, completion_tokens)
        else:
            # Fall back to standard model cost estimation
            from app.core.ai_config import ai_settings
            cost = estimate_cost(ai_settings.GROQ_MODEL, prompt_tokens, completion_tokens)
            
        meta = dict(state.metadata or {})
        meta["estimated_cost"] = cost
        
        return {
            "current_node": TELEMETRY_NODE,
            "previous_node": state.current_node,
            "execution_trace": trace,
            "metadata": meta
        }
