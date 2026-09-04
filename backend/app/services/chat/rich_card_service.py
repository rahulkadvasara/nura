"""
Nura - Rich Card Service
Converts structured resolved context objects into standardized rich cards list
"""

from datetime import datetime
from typing import List, Dict, Any
from app.schemas.chat import (
    RichCardResponse,
    ReportCard,
    MedicationCard,
    AppointmentCard,
    ReminderCard,
    DoctorCard,
    RiskCard,
    LaboratoryCard
)
from app.services.chat.action_builder import ActionBuilder


class RichCardService:
    """Builds list of rich healthcare cards from context structures"""

    def build_cards(self, resolved_context: Dict[str, Any], user_query: str = "") -> List[RichCardResponse]:
        cards: List[RichCardResponse] = []
        query_str = (user_query or str(resolved_context.get("query", ""))).lower()

        # 1. Report Cards
        if "reports" in resolved_context:
            for rep in resolved_context["reports"][:2]:
                cards.append(
                    ReportCard(
                        card_type="report",
                        title=rep.document_type or "Medical Report",
                        subtitle=rep.created_at.strftime("%B %d, %Y") if rep.created_at else None,
                        icon="FileText",
                        status=rep.risk_level.value if hasattr(rep.risk_level, "value") else str(rep.risk_level),
                        summary=rep.ai_summary or "Extracted medical diagnostics report.",
                        metadata={"report_id": rep.id},
                        actions=[
                            ActionBuilder.open_report(rep.id),
                            ActionBuilder.download_report(rep.id)
                        ]
                    )
                )

        # 2. Medication / Drug Safety Cards
        if "prescriptions" in resolved_context:
            for pr in resolved_context["prescriptions"][:2]:
                for med in pr.medications[:3]:
                    cards.append(
                        MedicationCard(
                            card_type="medication",
                            title=med.drug_name,
                            subtitle=f"Dosage: {med.dosage}",
                            icon="Pill",
                            status="active",
                            summary=f"Frequency: {med.frequency}. Instructions: {med.instructions or 'None'}",
                            metadata={"prescription_id": pr.id},
                            actions=[
                                ActionBuilder.view_medication(),
                                ActionBuilder.check_drug_safety()
                            ]
                        )
                    )

        if "drug_safety" in resolved_context:
            safety = resolved_context["drug_safety"]
            if safety.get("active_interaction_count", 0) > 0 or safety.get("interaction_findings"):
                cards.append(
                    RichCardResponse(
                        card_type="drug_safety",
                        title="Drug Interaction Warning",
                        subtitle=f"Overall Severity: {safety.get('overall_severity', 'NONE')}",
                        icon="AlertTriangle",
                        status=safety.get("overall_severity", "NONE"),
                        summary=safety.get("summary") or "Interaction risk detected on active medications.",
                        metadata=safety,
                        actions=[
                            ActionBuilder.check_drug_safety()
                        ]
                    )
                )

        # 3. Appointment Cards
        if "appointments" in resolved_context:
            is_active_query = any(kw in query_str for kw in ["active", "upcoming", "future", "scheduled", "open", "pending"])
            is_history_query = any(kw in query_str for kw in ["past", "history", "completed", "previous"])

            all_appts = resolved_context["appointments"]
            valid_appts = []
            for appt in all_appts:
                st_obj = getattr(appt, "status", "")
                st_val = (st_obj.value if hasattr(st_obj, "value") else str(st_obj)).lower()
                if (is_active_query or not is_history_query) and st_val not in ["approved", "pending", "scheduled", "in_progress"]:
                    continue
                valid_appts.append(appt)

            for appt in valid_appts[:5]:
                cards.append(
                    AppointmentCard(
                        card_type="appointment",
                        title="Doctor Consultation",
                        subtitle=f"{appt.slot_date} at {appt.slot_time}",
                        icon="Calendar",
                        status=appt.status.value if hasattr(appt.status, "value") else str(appt.status),
                        summary=appt.reason or "Clinical review consultation.",
                        metadata={"appointment_id": appt.id},
                        actions=[
                            ActionBuilder.book_appointment()
                        ]
                    )
                )

        # 4. Reminder Cards
        if "reminders" in resolved_context:
            for rem in resolved_context["reminders"][:2]:
                sched_str = rem.scheduled_time
                if isinstance(sched_str, datetime):
                    sched_str = sched_str.strftime('%I:%M %p')
                cards.append(
                    ReminderCard(
                        card_type="reminder",
                        title=rem.title,
                        subtitle=f"Schedule: {sched_str or 'None'}",
                        icon="Bell",
                        status=rem.status.value if hasattr(rem.status, "value") else str(rem.status),
                        summary=rem.description or "Configured daily reminder.",
                        metadata={"reminder_id": rem.id},
                        actions=[
                            ActionBuilder.view_reminder()
                        ]
                    )
                )

        # 5. Doctor Profile Cards
        if "doctors" in resolved_context:
            for doc in resolved_context["doctors"][:2]:
                doc_id = str(getattr(doc, "id", ""))
                raw_name = getattr(doc, "name", None) or getattr(doc, "full_name", None)
                if not raw_name or (isinstance(raw_name, str) and len(raw_name) == 24 and all(c in "0123456789abcdefABCDEF" for c in raw_name)):
                    raw_name = getattr(doc, "specialization", None) or "Medical Specialist"
                title_raw = str(raw_name).strip()
                if title_raw.startswith("Dr.") or title_raw.startswith("Doctor"):
                    title_str = title_raw
                else:
                    title_str = f"Dr. {title_raw}"
                specialization = getattr(doc, "specialization", None) or "General Medicine"
                fee = getattr(doc, "consultation_fee", 0) or 0
                avail = getattr(doc, "available_days", None) or getattr(doc, "availability_days", None) or "Weekdays"
                profile_st = getattr(doc, "profile_status", "ACTIVE")
                status_str = profile_st.value if hasattr(profile_st, "value") else str(profile_st)

                cards.append(
                    DoctorCard(
                        card_type="doctor",
                        title=title_str,
                        subtitle=specialization,
                        icon="UserCheck",
                        status=status_str,
                        summary=f"Consultation Fee: ₹{fee}. Availability: {avail}",
                        metadata={"doctor_id": doc_id},
                        actions=[
                            ActionBuilder.view_doctor(doc_id),
                            ActionBuilder.book_appointment()
                        ]
                    )
                )

        # 6. Laboratory Cards
        if "laboratory_results" in resolved_context:
            labs = resolved_context["laboratory_results"]
            rep_id = resolved_context.get("lab_report_id", "")
            for test in labs[:3]:
                cards.append(
                    LaboratoryCard(
                        card_type="laboratory",
                        title=test.get("name") or test.get("test_name") or "Lab Test",
                        subtitle=f"Value: {test.get('value')} {test.get('unit', '')}",
                        icon="Activity",
                        status=test.get("status") or "Normal",
                        summary=f"Reference Range: {test.get('reference_range') or 'N/A'}",
                        metadata={"report_id": rep_id},
                        actions=[
                            ActionBuilder.view_laboratory_results(rep_id)
                        ]
                    )
                )

        # 7. Risk Cards
        if "risks" in resolved_context:
            risks = resolved_context["risks"]
            rep_id = resolved_context.get("risk_report_id", "")
            for find in risks[:2]:
                cards.append(
                    RiskCard(
                        card_type="risk",
                        title=find.get("condition") or find.get("finding_name") or "Clinical Risk Findings",
                        subtitle=f"Risk Level: {find.get('severity') or find.get('risk_level', 'LOW')}",
                        icon="ShieldAlert",
                        status=find.get("severity") or find.get("risk_level", "LOW"),
                        summary=find.get("description") or find.get("recommendation") or "Clinical risk analysis identified markers.",
                        metadata={"report_id": rep_id},
                        actions=[
                            ActionBuilder.view_risk_analysis(rep_id)
                        ]
                    )
                )

        return cards

    async def resolve_and_build_cards(self, patient_id: str, message: str) -> List[RichCardResponse]:
        """Resolves context and builds rich cards list for patient and message query"""
        from app.core.dependencies import get_context_resolver
        resolver = get_context_resolver()
        resolved = await resolver.resolve_context(patient_id, message)
        return self.build_cards(resolved, user_query=message)
