"""
Nura - Reminder Agent
Orchestrates medication, appointment, and custom reminders workflows with integrated safety validations
"""

import time
import logging
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.base.response import AgentResponse
from app.agents.operations.schemas import ReminderAgentResponse
from app.agents.operations.telemetry import get_operations_telemetry
from app.agents.operations.utils import parse_llm_json_response
from app.core.ai_config import ai_settings
from app.services.reminder_service import ReminderService
from app.schemas.reminder import ReminderCreateSchema, ReminderUpdateSchema
from app.models.reminder import ReminderType, ReminderStatus, ReminderSourceType
from app.prompts.loader import PromptLoader

logger = logging.getLogger("nura.agents.operations.reminder_agent")


class ReminderAgent(BaseAgent):
    """Production operational agent for creating and managing patient reminders with drug safety checks"""

    def __init__(
        self,
        reminder_service: ReminderService,
        prompt_loader: Optional[PromptLoader] = None,
        settings=None
    ):
        super().__init__(name="ReminderAgent", settings=settings or ai_settings)
        self.reminder_service = reminder_service
        self.prompt_loader = prompt_loader or PromptLoader()
        self.telemetry = get_operations_telemetry()

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Processes query, parses structured actions (JSON) via LLM, and runs service orchestrations
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        
        if not patient_id:
            return AgentResponse(
                success=False,
                message="Execution aborted: Context patient_id is required for operational reminder actions.",
                execution_time=0.0,
                agent_name=self.name
            )

        # 1. Fetch patient profile, active reminders to populate LLM user template
        active_reminders_list = []
        patient_name = "Patient"
        clinical_summaries = "No current clinical summary."
        current_medications = "None"
        
        # Load patient context variables if service available
        try:
            from app.core.dependencies import get_patient_context_service
            ctx_svc = get_patient_context_service()
            patient_ctx = await ctx_svc.assemble_context(patient_id)
            if patient_ctx:
                patient_name = patient_ctx.patient_profile.get("full_name", "Patient")
                clinical_summaries = patient_ctx.medical_summary or "No chronic summaries."
                current_medications = ", ".join(patient_ctx.current_medications) if patient_ctx.current_medications else "None"
        except Exception as e:
            logger.warning(f"Failed to assemble patient context for ReminderAgent: {e}")

        # Fetch patient active reminders
        try:
            reminders = await self.reminder_service.list_active_reminders(patient_id)
            for r in reminders:
                active_reminders_list.append(
                    f"- ID: {r.id} | Type: {r.reminder_type.value} | Title: {r.title} | Time: {r.scheduled_time} | Recurrence: {r.recurrence or 'none'}"
                )
        except Exception as e:
            logger.warning(f"Failed to fetch reminders for patient {patient_id}: {e}")

        active_reminders_str = "\n".join(active_reminders_list) if active_reminders_list else "No active reminders."

        # 2. Render prompt templates and generate LLM call
        variables = {
            "patient_name": patient_name,
            "clinical_summaries": clinical_summaries,
            "current_medications": current_medications,
            "active_reminders": active_reminders_str,
            "query": query
        }

        system_prompt = self.prompt_loader.get_template("reminder_system", is_system=True)
        user_prompt = self.prompt_loader.render("reminder_user", variables, is_system=False)

        llm_response = await self.ai_service.generate(
            system_prompt=system_prompt,
            prompt=user_prompt
        )

        parsed_json = parse_llm_json_response(llm_response.response)
        if not parsed_json or "action" not in parsed_json:
            # Fallback to general explanation if LLM output fails parsing
            parsed_json = {"action": "explain_schedule", "parameters": {}}

        action = parsed_json["action"]
        params = parsed_json.get("parameters") or {}
        
        warnings = []
        safety_details = None
        created_rec = None
        updated_rec = None
        deleted_ref = None
        status = "success"
        message = ""
        service_calls = 1

        try:
            # 3. Handle Actions
            if action == "create_medication_reminder":
                medication = params.get("medication_name") or params.get("title") or "medication"
                
                # Programmatically run safety verification using DrugInteractionAgent
                try:
                    from app.core.dependencies import get_drug_interaction_agent
                    drug_agent = get_drug_interaction_agent()
                    service_calls += 1
                    # Pass clinical checking query
                    drug_res = await drug_agent.run(f"Check safety parameters for: {medication}", context)
                    if drug_res.success:
                        safety_details = drug_res.response.model_dump() if hasattr(drug_res.response, "model_dump") else drug_res.response
                        interaction_found = safety_details.get("interaction_found", False)
                        severity = safety_details.get("severity", "LOW")
                        
                        if interaction_found:
                            if severity in ("HIGH", "CRITICAL"):
                                # Strict block for patient safety
                                status = "failed"
                                warnings = safety_details.get("warnings", [])
                                message = f"Blocked: Medication reminder creation aborted due to {severity} drug interaction risk. Please consult your physician."
                                return AgentResponse(
                                    success=False,
                                    message=message,
                                    response=ReminderAgentResponse(
                                        status=status,
                                        action=action,
                                        message=message,
                                        warnings=warnings,
                                        safety_check_details=safety_details,
                                        usage={"prompt_tokens": llm_response.prompt_tokens, "completion_tokens": llm_response.completion_tokens, "total_tokens": llm_response.total_tokens},
                                        metadata={"patient_id": patient_id}
                                    ),
                                    execution_time=time.perf_counter() - start_time,
                                    agent_name=self.name
                                )
                            else:
                                status = "warned"
                                warnings = safety_details.get("warnings", [])
                except Exception as ex:
                    logger.error(f"Error checking drug interactions for medication {medication}: {ex}")
                    warnings.append(f"Failed to programmatically verify drug safety check: {str(ex)}")

                # Create medication reminder schema
                schema = ReminderCreateSchema(
                    patient_id=patient_id,
                    reminder_type=ReminderType.MEDICATION,
                    title=params.get("title") or f"Take {medication}",
                    description=params.get("description") or f"Auto-scheduled medication reminder for {medication}",
                    scheduled_time=params.get("scheduled_time") or "09:00",
                    recurrence=params.get("recurrence") or "daily",
                    status=ReminderStatus.ACTIVE,
                    source_type=ReminderSourceType.MANUAL
                )
                res_db = await self.reminder_service.create_reminder(schema)
                created_rec = self.reminder_service.to_response(res_db).model_dump()
                message = f"Medication reminder successfully created for {medication}."
                if status == "warned":
                    message += " Alert: Warnings are associated with this medication."

            elif action == "create_appointment_reminder":
                schema = ReminderCreateSchema(
                    patient_id=patient_id,
                    reminder_type=ReminderType.APPOINTMENT,
                    title=params.get("title") or "Upcoming Appointment",
                    description=params.get("description") or "Scheduled appointment reminder",
                    scheduled_time=params.get("scheduled_time") or "09:00",
                    recurrence=params.get("recurrence") or "once",
                    status=ReminderStatus.ACTIVE,
                    source_type=ReminderSourceType.MANUAL
                )
                res_db = await self.reminder_service.create_reminder(schema)
                created_rec = self.reminder_service.to_response(res_db).model_dump()
                message = "Appointment reminder created successfully."

            elif action == "create_custom_reminder":
                schema = ReminderCreateSchema(
                    patient_id=patient_id,
                    reminder_type=ReminderType.CUSTOM,
                    title=params.get("title") or "Custom Reminder Alert",
                    description=params.get("description"),
                    scheduled_time=params.get("scheduled_time") or "09:00",
                    recurrence=params.get("recurrence") or "daily",
                    status=ReminderStatus.ACTIVE,
                    source_type=ReminderSourceType.MANUAL
                )
                res_db = await self.reminder_service.create_reminder(schema)
                created_rec = self.reminder_service.to_response(res_db).model_dump()
                message = "Custom wellness reminder created successfully."

            elif action == "update_reminder":
                reminder_id = params.get("reminder_id")
                if not reminder_id:
                    raise ValueError("reminder_id parameter is required to update reminders")
                
                # Fetch first to ensure it belongs to the patient
                existing = await self.reminder_service.get_reminder_by_id(reminder_id)
                if not existing or existing.patient_id != patient_id:
                    raise ValueError(f"Reminder with ID {reminder_id} not found or access denied")

                schema = ReminderUpdateSchema(
                    title=params.get("title"),
                    description=params.get("description"),
                    scheduled_time=params.get("scheduled_time"),
                    recurrence=params.get("recurrence")
                )
                res_db = await self.reminder_service.update_reminder(reminder_id, schema)
                if res_db:
                    updated_rec = self.reminder_service.to_response(res_db).model_dump()
                    message = f"Reminder with ID {reminder_id} updated successfully."
                else:
                    raise RuntimeError("Failed to update reminder")

            elif action == "delete_reminder":
                reminder_id = params.get("reminder_id")
                if not reminder_id:
                    raise ValueError("reminder_id parameter is required to delete reminders")

                existing = await self.reminder_service.get_reminder_by_id(reminder_id)
                if not existing or existing.patient_id != patient_id:
                    raise ValueError(f"Reminder with ID {reminder_id} not found or access denied")

                success = await self.reminder_service.delete_reminder(reminder_id)
                if success:
                    deleted_ref = reminder_id
                    message = f"Reminder with ID {reminder_id} deleted successfully."
                else:
                    raise RuntimeError("Failed to delete reminder")

            elif action == "complete_reminder":
                reminder_id = params.get("reminder_id")
                if not reminder_id:
                    raise ValueError("reminder_id parameter is required to complete reminders")

                existing = await self.reminder_service.get_reminder_by_id(reminder_id)
                if not existing or existing.patient_id != patient_id:
                    raise ValueError(f"Reminder with ID {reminder_id} not found or access denied")

                schema = ReminderUpdateSchema(status=ReminderStatus.COMPLETED)
                res_db = await self.reminder_service.update_reminder(reminder_id, schema)
                if res_db:
                    updated_rec = self.reminder_service.to_response(res_db).model_dump()
                    message = f"Reminder with ID {reminder_id} marked as completed."
                else:
                    raise RuntimeError("Failed to complete reminder")

            else:  # explain_schedule
                # Describe patient schedule
                if active_reminders_list:
                    message = f"You have {len(active_reminders_list)} active reminders scheduled:\n" + "\n".join(active_reminders_list)
                else:
                    message = "You have no active reminders scheduled at this time."

        except Exception as e:
            status = "failed"
            message = f"Failed to execute reminder operation: {str(e)}"
            logger.error(f"Reminder operation failure: {e}")
            return AgentResponse(
                success=False,
                message=message,
                execution_time=time.perf_counter() - start_time,
                agent_name=self.name
            )

        elapsed = time.perf_counter() - start_time
        
        # 4. Formulate response object
        response_model = ReminderAgentResponse(
            status=status,
            action=action,
            message=message,
            created_reminder=created_rec,
            updated_reminder=updated_rec,
            deleted_id=deleted_ref,
            warnings=warnings,
            safety_check_details=safety_details,
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
            message="Reminder operation processed successfully",
            response=response_model,
            execution_time=elapsed * 1000,
            agent_name=self.name
        )
