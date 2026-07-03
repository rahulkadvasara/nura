"""
Nura - Deep Link Service
Generates navigation targets for structured cards pointing to existing dashboard pages
"""

class DeepLinkService:
    """Provides navigation routes mapping clinical resources to dashboard viewports"""

    @staticmethod
    def get_report_link(report_id: str) -> str:
        return f"/dashboard/records/{report_id}"

    @staticmethod
    def get_reminder_link() -> str:
        return "/dashboard/reminders"

    @staticmethod
    def get_appointment_link() -> str:
        return "/dashboard/appointments"

    @staticmethod
    def get_doctor_link(doctor_id: str) -> str:
        return f"/dashboard/doctors/{doctor_id}"

    @staticmethod
    def get_drug_safety_link() -> str:
        return "/dashboard/patient"

    @staticmethod
    def get_risk_analysis_link(report_id: str) -> str:
        return f"/dashboard/records/{report_id}"
