"""
Nura - Operational Agents Response Schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ReminderAgentResponse(BaseModel):
    """Structured response schema returned by the ReminderAgent"""
    status: str = Field(..., description="Execution status: success, failed, or warning")
    action: str = Field(..., description="Action executed: create_medication, create_appointment, create_custom, update, delete, complete, explain")
    message: str = Field(..., description="Narrative summary describing execution results")
    created_reminder: Optional[Dict[str, Any]] = Field(None, description="Metadata of created reminder record")
    updated_reminder: Optional[Dict[str, Any]] = Field(None, description="Metadata of updated reminder record")
    deleted_id: Optional[str] = Field(None, description="Deleted reminder ID reference")
    warnings: List[str] = Field(default_factory=list, description="Safety alerts or drug interaction warnings")
    safety_check_details: Optional[Dict[str, Any]] = Field(None, description="Verbose logs from DrugInteractionAgent checks")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM token usage counters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context parameters")


class AppointmentAgentResponse(BaseModel):
    """Structured response schema returned by the AppointmentAgent"""
    status: str = Field(..., description="Execution status: success or failed")
    action: str = Field(..., description="Action executed: search_doctors, recommend_slots, book_appointment, reschedule_appointment, cancel_appointment, explain_status")
    message: str = Field(..., description="Narrative summary describing execution results")
    search_results: Optional[List[Dict[str, Any]]] = Field(None, description="Found doctor profiles discovery schemas")
    slots: Optional[List[Dict[str, Any]]] = Field(None, description="Available date/time booking slots")
    appointment: Optional[Dict[str, Any]] = Field(None, description="Created or cancelled appointment record details")
    rescheduled_appointment: Optional[Dict[str, Any]] = Field(None, description="New rescheduled appointment record details")
    cancelled_id: Optional[str] = Field(None, description="Cancelled appointment ID reference")
    reasoning: Optional[str] = Field(None, description="Reasoning narrative explaining doctor match/action selection")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM token usage counters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context parameters")
