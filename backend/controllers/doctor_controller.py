"""
doctor_controller.py – Routes for Doctor dashboard operations.
"""
import json
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.auth.rbac import require_doctor, require_medical_staff, require_roles, CurrentUser
from backend.repositories.doctor_repo import DoctorRepository
from backend.repositories.appointment_repo import AppointmentRepository
from backend.repositories.medical_record_repo import MedicalRecordRepository
from backend.repositories.audit_repo import AuditRepository
from backend.services.appointment_service import AppointmentService
from backend.services.queue_service import QueueService

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


# ── Doctor profile ─────────────────────────────────────────────────────────────
@router.get("/me")
async def get_my_profile(
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    doctor = DoctorRepository.get_by_user_id(current_user.user_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return doctor


@router.get("/public")
async def list_doctors_public(specialization: Optional[str] = Query(None)):
    """Public endpoint — no auth required. Used on the registration page."""
    return DoctorRepository.list_doctors(specialization)


@router.get("/list")
async def list_doctors(
    specialization: Optional[str] = Query(None),
    current_user: Annotated[CurrentUser, Depends(require_roles("Admin", "Doctor", "Patient", "Pharmacist", "LabTech"))] = None,
):
    return DoctorRepository.list_doctors(specialization)


# ── Appointments ───────────────────────────────────────────────────────────────
@router.get("/appointments")
async def get_my_appointments(
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
    status: Optional[str] = Query(None),
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    doctor = DoctorRepository.get_by_user_id(current_user.user_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    appointments = AppointmentRepository.get_doctor_appointments(doctor["id"], status, date)
    AuditRepository.log(
        action="VIEW",
        target_table="Appointments",
        user_id=current_user.user_id,
    )
    return appointments


@router.post("/appointments/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: int,
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    return AppointmentService.complete_appointment(appointment_id, current_user.user_id)


# ── Queue ──────────────────────────────────────────────────────────────────────
@router.get("/queue")
async def get_queue(
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    doctor = DoctorRepository.get_by_user_id(current_user.user_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return QueueService.estimate_wait_time(doctor["id"])


# ── Medical Records ────────────────────────────────────────────────────────────
class UpdateRecordBody(BaseModel):
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescriptions: Optional[list] = None


@router.get("/records/{record_id}")
async def get_record(
    record_id: int,
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    record = MedicalRecordRepository.get_full(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    AuditRepository.log(
        action="VIEW",
        target_table="Medical_Records",
        target_id=record_id,
        user_id=current_user.user_id,
    )
    # Deserialise JSON columns
    if record.get("prescriptions") and isinstance(record["prescriptions"], str):
        record["prescriptions"] = json.loads(record["prescriptions"])
    return record


@router.patch("/records/{record_id}")
async def update_record(
    record_id: int,
    body: UpdateRecordBody,
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    MedicalRecordRepository.update_notes_and_diagnosis(
        record_id, body.notes, body.diagnosis
    )
    if body.prescriptions is not None:
        MedicalRecordRepository.update_prescriptions(record_id, body.prescriptions)
    AuditRepository.log(
        action="UPDATE",
        target_table="Medical_Records",
        target_id=record_id,
        user_id=current_user.user_id,
        details={"fields_updated": [k for k, v in body.model_dump().items() if v is not None]},
    )
    return {"status": "updated", "record_id": record_id}


@router.get("/patients/{patient_id}/history")
async def get_patient_history(
    patient_id: int,
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    records = MedicalRecordRepository.get_by_patient(patient_id)
    AuditRepository.log(
        action="VIEW",
        target_table="Medical_Records",
        user_id=current_user.user_id,
        details={"patient_id": patient_id},
    )
    for r in records:
        if r.get("prescriptions") and isinstance(r["prescriptions"], str):
            r["prescriptions"] = json.loads(r["prescriptions"])
    return records
