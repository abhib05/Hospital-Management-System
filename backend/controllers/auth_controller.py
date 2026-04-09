"""
auth_controller.py – FastAPI router for /api/auth endpoints.
Controller layer: validates input, delegates to AuthService.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from backend.services.auth_service import AuthService
from backend.repositories.patient_repo import PatientRepository
from backend.repositories.appointment_repo import AppointmentRepository
from backend.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

VALID_ROLES = {"Admin", "Doctor", "Patient", "Pharmacist", "LabTech"}


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8, max_length=128)
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in VALID_ROLES:
            raise ValueError(f"role must be one of {VALID_ROLES}")
        return v


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    ip = request.client.host if request.client else None
    try:
        return AuthService.login(body.username, body.password, ip)
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse
        if isinstance(e, HTTPException): raise e
        return JSONResponse(status_code=500, content={"detail": error_msg})



@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Admin-only in production; open here for demo."""
    return AuthService.register(body.username, body.password, body.role)


class RegisterPatientRequest(BaseModel):
    # Account
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8, max_length=128)
    # Personal info
    full_name: str = Field(..., min_length=2, max_length=120)
    dob: str = Field(..., description="YYYY-MM-DD")
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    # First appointment
    doctor_id: int
    scheduled_at: datetime
    reason: Optional[str] = None


@router.post("/register-patient", status_code=201)
async def register_patient(body: RegisterPatientRequest):
    """
    One-shot patient registration:
      1. Create User record
      2. Create Patient profile
      3. Book first appointment
      4. Return JWT so the patient is auto-logged-in
    """
    # 1. Create the user account
    result = AuthService.register(body.username, body.password, "Patient")
    user_id = result["user_id"]

    # 2. Create the patient profile
    patient_id = PatientRepository.create(
        user_id=user_id,
        full_name=body.full_name,
        dob=body.dob,
        gender=body.gender,
        phone=body.phone,
        blood_group=body.blood_group,
    )

    # 3. Book the first appointment
    appointment_id = AppointmentRepository.book_appointment(
        patient_id=patient_id,
        doctor_id=body.doctor_id,
        scheduled_at=body.scheduled_at,
        reason=body.reason,
    )

    # 4. Issue JWT so the frontend can auto-login
    token = create_access_token(
        user_id=user_id,
        username=body.username,
        role="Patient",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": body.username,
        "role": "Patient",
        "patient_id": patient_id,
        "appointment_id": appointment_id,
    }
