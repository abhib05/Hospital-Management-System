"""
queue_service.py – Wait-time estimator based on scheduled appointments.
Assumes an average consultation of 15 minutes per patient.
"""
from backend.repositories.appointment_repo import AppointmentRepository

AVG_CONSULTATION_MINUTES = 15


class QueueService:

    @staticmethod
    def estimate_wait_time(doctor_id: int) -> dict:
        """
        Returns the number of patients ahead in the current hour
        and an estimated wait time in minutes.
        """
        count = AppointmentRepository.count_scheduled_this_hour(doctor_id)
        estimated_minutes = count * AVG_CONSULTATION_MINUTES
        return {
            "patients_in_queue": count,
            "estimated_wait_minutes": estimated_minutes,
            "avg_consultation_minutes": AVG_CONSULTATION_MINUTES,
        }
