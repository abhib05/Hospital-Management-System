"""
admin_controller.py – Admin-only routes: user management, audit logs, inventory CRUD.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.auth.rbac import require_admin, CurrentUser
from backend.repositories.user_repo import UserRepository
from backend.repositories.audit_repo import AuditRepository
from backend.repositories.inventory_repo import InventoryRepository
from backend.repositories.doctor_repo import DoctorRepository
from backend.repositories.patient_repo import PatientRepository
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Users ──────────────────────────────────────────────────────────────────────
@router.get("/users")
async def list_users(
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    role: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    return UserRepository.list_users(role, limit, offset)


@router.delete("/users/{user_id}")
async def soft_delete_user(
    user_id: int,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
):
    user = UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    UserRepository.soft_delete(user_id)
    AuditRepository.log(
        action="DELETE",
        target_table="Users",
        target_id=user_id,
        user_id=current_user.user_id,
    )
    return {"status": "soft-deleted", "user_id": user_id}


# ── Audit Logs ─────────────────────────────────────────────────────────────────
@router.get("/audit-logs")
async def get_audit_logs(
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    user_id: Optional[int] = Query(None),
    target_table: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    return AuditRepository.get_logs(user_id, target_table, action, limit, offset)


# ── Inventory management ───────────────────────────────────────────────────────
@router.get("/inventory")
async def list_inventory(
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    include_inactive: bool = Query(False),
):
    return InventoryRepository.get_all(include_inactive=include_inactive)


class InventoryCreateBody(BaseModel):
    drug_name: str = Field(..., min_length=2)
    generic_name: Optional[str] = None
    unit: str = "tablet"
    unit_price: float = Field(..., gt=0)
    stock_qty: int = Field(0, ge=0)
    reorder_level: int = Field(10, ge=0)


@router.post("/inventory", status_code=201)
async def add_inventory_item(
    body: InventoryCreateBody,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
):
    from backend.database import execute_query
    sql = """
        INSERT INTO Inventory
            (drug_name, generic_name, unit, unit_price, stock_qty, reorder_level)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    new_id = execute_query(
        sql,
        (body.drug_name, body.generic_name, body.unit,
         body.unit_price, body.stock_qty, body.reorder_level),
        last_row_id=True,
    )
    AuditRepository.log(
        action="CREATE",
        target_table="Inventory",
        target_id=new_id,
        user_id=current_user.user_id,
    )
    return {"id": new_id, **body.model_dump()}


@router.patch("/inventory/{item_id}/restock")
async def restock_item(
    item_id: int,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    qty: int = Query(..., gt=0),
):
    from backend.database import execute_query
    sql = "UPDATE Inventory SET stock_qty = stock_qty + %s WHERE id = %s"
    execute_query(sql, (qty, item_id))
    AuditRepository.log(
        action="UPDATE",
        target_table="Inventory",
        target_id=item_id,
        user_id=current_user.user_id,
        details={"restock_qty": qty},
    )
    return {"status": "restocked", "added_qty": qty}


# ── Doctor / Patient registration helpers ──────────────────────────────────────
class CreateDoctorBody(BaseModel):
    username: str
    password: str = Field(..., min_length=8)
    full_name: str
    specialization: str
    fees: float = Field(..., gt=0)
    phone: Optional[str] = None


@router.post("/doctors", status_code=201)
async def create_doctor(
    body: CreateDoctorBody,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
):
    user = AuthService.register(body.username, body.password, "Doctor")
    doctor_id = DoctorRepository.create(
        user["user_id"], body.full_name, body.specialization, body.fees, body.phone
    )
    return {"user_id": user["user_id"], "doctor_id": doctor_id}


class CreatePatientBody(BaseModel):
    username: str
    password: str = Field(..., min_length=8)
    full_name: str
    dob: str
    gender: str
    phone: Optional[str] = None
    blood_group: Optional[str] = None


@router.post("/patients", status_code=201)
async def create_patient(
    body: CreatePatientBody,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
):
    user = AuthService.register(body.username, body.password, "Patient")
    patient_id = PatientRepository.create(
        user_id=user["user_id"],
        full_name=body.full_name,
        dob=body.dob,
        gender=body.gender,
        phone=body.phone,
        blood_group=body.blood_group,
    )
    return {"user_id": user["user_id"], "patient_id": patient_id}
