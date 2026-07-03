"""
Nura - Action Builder
Standardized action payloads associated with dashboard operations
"""

from typing import Optional, Dict, Any
from app.schemas.chat import RichCardAction
from app.services.chat.deep_link_service import DeepLinkService


class ActionBuilder:
    """Helper class to construct standardized CTA triggers for frontend buttons"""

    @staticmethod
    def open_report(report_id: str) -> RichCardAction:
        return RichCardAction(
            action_type="OPEN_REPORT",
            label="Open Report",
            url=DeepLinkService.get_report_link(report_id)
        )

    @staticmethod
    def download_report(report_id: str) -> RichCardAction:
        return RichCardAction(
            action_type="DOWNLOAD_REPORT",
            label="Download Report",
            url=f"/api/v1/reports/{report_id}/download"
        )

    @staticmethod
    def view_doctor(doctor_id: str) -> RichCardAction:
        return RichCardAction(
            action_type="VIEW_DOCTOR",
            label="View Doctor",
            url=DeepLinkService.get_doctor_link(doctor_id)
        )

    @staticmethod
    def book_appointment() -> RichCardAction:
        return RichCardAction(
            action_type="BOOK_APPOINTMENT",
            label="Book Appointment",
            url=DeepLinkService.get_appointment_link()
        )

    @staticmethod
    def create_reminder() -> RichCardAction:
        return RichCardAction(
            action_type="CREATE_REMINDER",
            label="Create Reminder",
            url=DeepLinkService.get_reminder_link()
        )

    @staticmethod
    def view_reminder() -> RichCardAction:
        return RichCardAction(
            action_type="VIEW_REMINDER",
            label="View Reminder",
            url=DeepLinkService.get_reminder_link()
        )

    @staticmethod
    def view_medication() -> RichCardAction:
        return RichCardAction(
            action_type="VIEW_MEDICATION",
            label="View Medications",
            url="/dashboard/medications"
        )

    @staticmethod
    def check_drug_safety() -> RichCardAction:
        return RichCardAction(
            action_type="CHECK_DRUG_SAFETY",
            label="Check Safety",
            url=DeepLinkService.get_drug_safety_link()
        )

    @staticmethod
    def view_risk_analysis(report_id: str) -> RichCardAction:
        return RichCardAction(
            action_type="VIEW_RISK_ANALYSIS",
            label="View Analysis",
            url=DeepLinkService.get_risk_analysis_link(report_id)
        )

    @staticmethod
    def view_laboratory_results(report_id: str) -> RichCardAction:
        return RichCardAction(
            action_type="VIEW_LABORATORY_RESULTS",
            label="View Full Report",
            url=DeepLinkService.get_report_link(report_id)
        )
