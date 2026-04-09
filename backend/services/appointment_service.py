"""
appointment_service.py – Business logic for appointment lifecycle.
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from backend.repositories.appointment_repo import AppointmentRepository
from backend.repositories.doctor_repo import DoctorRepository
from backend.repositories.patient_repo import PatientRepository
from backend.repositories.medical_record_repo import MedicalRecordRepository
from backend.repositories.audit_repo import AuditRepository
from backend.services.billing_service import BillingService


class AppointmentService:

    @staticmethod
    def book(
        patient_id: int,
        doctor_id: int,
        scheduled_at: datetime,
        reason: Optional[str],
        actor_user_id: int,
    ) -> dict:
        # Validate entities exist
        if not DoctorRepository.get_by_id(doctor_id):
            raise HTTPException(status_code=404, detail="Doctor not found")
        if not PatientRepository.get_by_id(patient_id):
            raise HTTPException(status_code=404, detail="Patient not found")

        appt_id = AppointmentRepository.book_appointment(
            patient_id, doctor_id, scheduled_at, reason
        )
        AuditRepository.log(
            action="CREATE",
            target_table="Appointments",
            target_id=appt_id,
            user_id=actor_user_id,
            details={"patient_id": patient_id, "doctor_id": doctor_id},
        )
        return AppointmentRepository.get_by_id(appt_id)

    @staticmethod
    def complete_appointment(appointment_id: int, actor_user_id: int) -> dict:
        """
        Mark appointment Completed, create Medical_Record and Invoice.
        """
        appt = AppointmentRepository.get_by_id(appointment_id)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if appt["status"] != "Scheduled":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete appointment with status '{appt['status']}'",
            )
        AppointmentRepository.update_status(appointment_id, "Completed")

        # Auto-create medical record and invoice
        record_id = MedicalRecordRepository.create(
            appointment_id=appointment_id,
            patient_id=appt["patient_id"],
            doctor_id=appt["doctor_id"],
        )
        BillingService.generate_invoice(appointment_id, actor_user_id)

        AuditRepository.log(
            action="UPDATE",
            target_table="Appointments",
            target_id=appointment_id,
            user_id=actor_user_id,
            details={"new_status": "Completed", "record_id": record_id},
        )
        return {"appointment_id": appointment_id, "record_id": record_id, "status": "Completed"}
