"""
Nura - LangGraph Infrastructure Nodes
Infrastructure callables executing startup, initialization, router placeholder, and completion.
"""

import time
import uuid
from typing import Dict, Any
from app.graph.state import GraphState
from app.graph.constants import START_NODE, INIT_STATE_NODE, ROUTER_AGENT_NODE, FINISH_NODE


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
