"""
Nura - Appointment Agent
Orchestrates doctor searching, availability slot recommendation, booking, cancelling, and rescheduling of appointments
"""

import time
import logging
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.base.response import AgentResponse
from app.agents.operations.schemas import AppointmentAgentResponse
from app.agents.operations.telemetry import get_operations_telemetry
from app.agents.operations.utils import parse_llm_json_response
from app.core.ai_config import ai_settings
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorProfileService, DoctorAvailabilityService
from app.schemas.appointment import AppointmentCreateSchema, AppointmentUpdateSchema
from app.schemas.doctor import DoctorAvailabilityUpdateSchema
from app.prompts.loader import PromptLoader

logger = logging.getLogger("nura.agents.operations.appointment_agent")


class AppointmentAgent(BaseAgent):
    """Production operational agent for doctor discovery and scheduling operations"""

    def __init__(
        self,
        appointment_service: AppointmentService,
        doctor_service: DoctorProfileService,
        availability_service: DoctorAvailabilityService,
        prompt_loader: Optional[PromptLoader] = None,
        settings=None
    ):
        super().__init__(name="AppointmentAgent", settings=settings or ai_settings)
        self.appointment_service = appointment_service
        self.doctor_service = doctor_service
        self.availability_service = availability_service
        self.prompt_loader = prompt_loader or PromptLoader()
        self.telemetry = get_operations_telemetry()

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Processes query, parses structured actions (JSON) via LLM, and runs service calls
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()

        if not patient_id:
            return AgentResponse(
                success=False,
                message="Execution aborted: Context patient_id is required for operational appointment actions.",
                execution_time=0.0,
                agent_name=self.name
            )

        # 1. Fetch patient location and appointment history details to populate LLM user template
        patient_location = "New York, USA"
        patient_name = "Patient"
        specialist_recommendation = "None"
        history_list = []
        
        # Load patient context variables if service available
        try:
            from app.core.dependencies import get_patient_context_service
            ctx_svc = get_patient_context_service()
            patient_ctx = await ctx_svc.assemble_context(patient_id)
            if patient_ctx:
                patient_name = patient_ctx.patient_profile.get("full_name", "Patient")
                patient_location = patient_ctx.patient_profile.get("location") or "New York, USA"
        except Exception as e:
            logger.warning(f"Failed to assemble patient context for AppointmentAgent: {e}")

        # Try to retrieve recommended doctor specialization if referral history was analyzed previously
        if context and context.metadata:
            specialist_recommendation = context.metadata.get("doctor_recommendation", "None")

        # Fetch appointments history
        try:
            history = await self.appointment_service.list_patient_appointments_history(patient_id)
            for h in history:
                history_list.append(
                    f"- Appointment ID: {h['id']} | Doctor: {h['doctor_name']} ({h['specialization']}) | Date: {h['appointment_date']} | Time: {h['appointment_time']} | Status: {h['status']}"
                )
        except Exception as e:
            logger.warning(f"Failed to fetch appointments history for patient {patient_id}: {e}")

        appointments_history_str = "\n".join(history_list) if history_list else "No existing appointment history."

        # 2. Render prompt templates and generate LLM call
        variables = {
            "patient_name": patient_name,
            "patient_location": patient_location,
            "specialist_recommendation": specialist_recommendation,
            "appointments_history": appointments_history_str,
            "query": query
        }

        system_prompt = self.prompt_loader.get_template("appointment_system", is_system=True)
        user_prompt = self.prompt_loader.render("appointment_user", variables, is_system=False)

        llm_response = await self.ai_service.generate(
            system_prompt=system_prompt,
            prompt=user_prompt
        )

        parsed_json = parse_llm_json_response(llm_response.response)
        if not parsed_json or "action" not in parsed_json:
            parsed_json = {"action": "explain_status", "parameters": {}}

        action = parsed_json["action"]
        params = parsed_json.get("parameters") or {}

        search_results = None
        slots = None
        appointment = None
        rescheduled_appt = None
        cancelled_ref = None
        reasoning = ""
        status = "success"
        message = ""
        service_calls = 1

        try:
            # 3. Handle Actions
            if action == "search_doctors":
                doc_name = params.get("doctor_name")
                spec = params.get("specialization")
                
                doctors = await self.doctor_service.search_verified_doctors(
                    name_query=doc_name,
                    specialization=spec
                )
                search_results = [d.model_dump() for d in doctors]
                message = f"Found {len(search_results)} matching doctors."
                reasoning = f"Searched doctor profiles in the directory matching name '{doc_name}' or specialty '{spec}'."

            elif action == "recommend_slots":
                doctor_id = params.get("doctor_id")
                if not doctor_id:
                    raise ValueError("doctor_id is required to fetch available slots")

                active_slots = await self.availability_service.get_active_availability(doctor_id)
                slots = [s.model_dump() for s in active_slots if s.is_available]
                message = f"Found {len(slots)} available slots for doctor with ID {doctor_id}."
                reasoning = "Retrieved active availability slots from the calendar database."

            elif action == "book_appointment":
                doctor_id = params.get("doctor_id")
                avail_id = params.get("availability_id")
                reason = params.get("reason") or "General Consultation"
                notes = params.get("notes")
                
                if not doctor_id or not avail_id:
                    raise ValueError("doctor_id and availability_id are required to book appointments")

                schema = AppointmentCreateSchema(
                    doctor_id=doctor_id,
                    availability_id=avail_id,
                    reason=reason,
                    notes=notes
                )
                res_db = await self.appointment_service.create_appointment(patient_id, schema)
                
                # Mark availability slot as booked/not available
                await self.availability_service.update_availability(
                    avail_id, 
                    DoctorAvailabilityUpdateSchema(is_available=False)
                )

                appointment = self.appointment_service.to_response(res_db).model_dump()
                message = "Appointment booked successfully."
                reasoning = f"Created pending appointment slot for Doctor ID {doctor_id}."

            elif action == "reschedule_appointment":
                appointment_id = params.get("appointment_id")
                new_avail_id = params.get("availability_id")
                reason = params.get("reason") or "Rescheduled appointment slot"
                
                if not appointment_id or not new_avail_id:
                    raise ValueError("appointment_id and availability_id are required to reschedule")

                # Fetch original appointment
                existing_appt = await self.appointment_service.get_appointment_by_id(appointment_id)
                if not existing_appt or existing_appt.patient_id != patient_id:
                    raise ValueError(f"Appointment with ID {appointment_id} not found or access denied")

                # Reschedule workflow consists of two steps:
                # 1. Cancel old appointment
                await self.appointment_service.cancel_patient_appointment(appointment_id, patient_id)
                # Re-activate old slot
                if existing_appt.availability_id:
                    await self.availability_service.update_availability(
                        existing_appt.availability_id,
                        DoctorAvailabilityUpdateSchema(is_available=True)
                    )
                service_calls += 1

                # 2. Book new appointment
                schema = AppointmentCreateSchema(
                    doctor_id=existing_appt.doctor_id,
                    availability_id=new_avail_id,
                    reason=reason
                )
                res_db = await self.appointment_service.create_appointment(patient_id, schema)
                # Mark new slot unavailable
                await self.availability_service.update_availability(
                    new_avail_id,
                    DoctorAvailabilityUpdateSchema(is_available=False)
                )
                service_calls += 1

                rescheduled_appt = self.appointment_service.to_response(res_db).model_dump()
                message = "Appointment rescheduled successfully."
                reasoning = f"Cancelled old appointment {appointment_id} and booked new slot {new_avail_id}."

            elif action == "cancel_appointment":
                appointment_id = params.get("appointment_id")
                if not appointment_id:
                    raise ValueError("appointment_id is required to cancel appointments")

                existing_appt = await self.appointment_service.get_appointment_by_id(appointment_id)
                if not existing_appt or existing_appt.patient_id != patient_id:
                    raise ValueError(f"Appointment with ID {appointment_id} not found or access denied")

                res_db = await self.appointment_service.cancel_patient_appointment(appointment_id, patient_id)
                # Re-activate availability slot
                if res_db and res_db.availability_id:
                    await self.availability_service.update_availability(
                        res_db.availability_id,
                        DoctorAvailabilityUpdateSchema(is_available=True)
                    )
                
                appointment = self.appointment_service.to_response(res_db).model_dump()
                cancelled_ref = appointment_id
                message = "Appointment cancelled successfully."
                reasoning = f"Cancelled pending appointment {appointment_id}."

            else:  # explain_status
                if history_list:
                    message = f"You have {len(history_list)} registered appointments:\n" + "\n".join(history_list)
                else:
                    message = "You have no appointments scheduled."
                reasoning = "Fetched appointments history from database."

        except Exception as e:
            status = "failed"
            message = f"Failed to execute appointment operation: {str(e)}"
            logger.error(f"Appointment operation failure: {e}")
            return AgentResponse(
                success=False,
                message=message,
                execution_time=time.perf_counter() - start_time,
                agent_name=self.name
            )

        elapsed = time.perf_counter() - start_time

        # 4. Formulate response object
        response_model = AppointmentAgentResponse(
            status=status,
            action=action,
            message=message,
            search_results=search_results,
            slots=slots,
            appointment=appointment,
            rescheduled_appointment=rescheduled_appt,
            cancelled_id=cancelled_ref,
            reasoning=reasoning,
            usage={
                "prompt_tokens": llm_response.prompt_tokens,
                "completion_tokens": llm_response.completion_tokens,
                "total_tokens": llm_response.total_tokens
            },
            metadata={"patient_id": patient_id}
        )

        # Record Telemetry
        self.telemetry.record_execution(
            agent_name=self.name,
            success=(status != "failed"),
            latency_ms=elapsed * 1000,
            tokens=llm_response.total_tokens,
            cost=llm_response.estimated_cost,
            service_calls=service_calls
        )

        return AgentResponse(
            success=True,
            message="Appointment operation processed successfully",
            response=response_model,
            execution_time=elapsed * 1000,
            agent_name=self.name
        )
