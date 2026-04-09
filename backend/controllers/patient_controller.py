"""
patient_controller.py – Patient portal routes.
Sensitive data is masked until re-authentication or explicit 'view' action.
"""
import json
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.auth.rbac import require_patient, require_doctor, get_current_user, CurrentUser
from backend.repositories.patient_repo import PatientRepository
from backend.repositories.appointment_repo import AppointmentRepository
from backend.repositories.invoice_repo import InvoiceRepository
from backend.repositories.doctor_repo import DoctorRepository
from backend.repositories.audit_repo import AuditRepository
from backend.services.appointment_service import AppointmentService

router = APIRouter(prefix="/api/patients", tags=["Patients"])


def _mask_patient(record: dict) -> dict:
    """
    Mask sensitive fields by default.
    Full values returned only when the caller explicitly requests them
    (triggering an Audit_Log entry).
    """
    masked = dict(record)
    if masked.get("phone"):
        masked["phone"] = masked["phone"][:4] + "****"
    if masked.get("address"):
        masked["address"] = "****"
    if masked.get("medical_history"):
        masked["medical_history"] = "****"
    return masked


# ── Patient self-view ──────────────────────────────────────────────────────────
@router.get("/me")
async def get_my_profile(
    current_user: Annotated[CurrentUser, Depends(require_patient)],
):
    patient = PatientRepository.get_by_user_id(current_user.user_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return _mask_patient(patient)


@router.get("/me/full")
async def get_my_full_profile(
    current_user: Annotated[CurrentUser, Depends(require_patient)],
):
    """Full profile — triggers audit log entry as per requirement."""
    patient = PatientRepository.get_by_user_id(current_user.user_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    AuditRepository.log(
        action="VIEW",
        target_table="Patients",
        target_id=patient["id"],
        user_id=current_user.user_id,
        details={"view": "full_profile_reveal"},
    )
    if patient.get("medical_history") and isinstance(patient["medical_history"], str):
        patient["medical_history"] = json.loads(patient["medical_history"])
    return patient


@router.get("/me/appointments")
async def my_appointments(
    current_user: Annotated[CurrentUser, Depends(require_patient)],
):
    patient = PatientRepository.get_by_user_id(current_user.user_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return AppointmentRepository.get_patient_appointments(patient["id"])


@router.get("/me/invoices")
async def my_invoices(
    current_user: Annotated[CurrentUser, Depends(require_patient)],
):
    patient = PatientRepository.get_by_user_id(current_user.user_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    AuditRepository.log(
        action="VIEW",
        target_table="Invoices",
        user_id=current_user.user_id,
    )
    return InvoiceRepository.get_patient_invoices(patient["id"])


# ── Booking ────────────────────────────────────────────────────────────────────
class BookAppointmentBody(BaseModel):
    doctor_id: int
    scheduled_at: datetime
    reason: Optional[str] = None


@router.post("/me/appointments", status_code=201)
async def book_appointment(
    body: BookAppointmentBody,
    current_user: Annotated[CurrentUser, Depends(require_patient)],
):
    patient = PatientRepository.get_by_user_id(current_user.user_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return AppointmentService.book(
        patient_id=patient["id"],
        doctor_id=body.doctor_id,
        scheduled_at=body.scheduled_at,
        reason=body.reason,
        actor_user_id=current_user.user_id,
    )


# ── Doctor-accessible patient list ────────────────────────────────────────────
@router.get("/list")
async def list_patients(
    search: Optional[str] = Query(None),
    current_user: Annotated[CurrentUser, Depends(require_doctor)] = None,
):
    return PatientRepository.list_patients(search)


@router.get("/{patient_id}")
async def get_patient_detail(
    patient_id: int,
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    patient = PatientRepository.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    AuditRepository.log(
        action="VIEW",
        target_table="Patients",
        target_id=patient_id,
        user_id=current_user.user_id,
    )
    if patient.get("medical_history") and isinstance(patient["medical_history"], str):
        patient["medical_history"] = json.loads(patient["medical_history"])
    return patient
