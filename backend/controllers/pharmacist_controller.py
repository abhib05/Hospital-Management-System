"""
pharmacist_controller.py – Routes for the Pharmacist dashboard.
CRITICAL: Medical record queries here NEVER return diagnosis/notes.
Access control is enforced at the SQL/service layer, not the frontend.
"""
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth.rbac import require_pharmacist, CurrentUser
from backend.repositories.medical_record_repo import MedicalRecordRepository
from backend.repositories.inventory_repo import InventoryRepository
from backend.repositories.audit_repo import AuditRepository
from backend.services.billing_service import BillingService

router = APIRouter(prefix="/api/pharmacist", tags=["Pharmacist"])


# ── Pending prescriptions ──────────────────────────────────────────────────────
@router.get("/prescriptions")
async def get_pending_prescriptions(
    current_user: Annotated[CurrentUser, Depends(require_pharmacist)],
):
    """
    Returns records with prescriptions — WITHOUT diagnosis or notes.
    Access restriction enforced in MedicalRecordRepository.get_pending_dispense().
    """
    records = MedicalRecordRepository.get_pending_dispense()
    for r in records:
        if r.get("prescriptions") and isinstance(r["prescriptions"], str):
            r["prescriptions"] = json.loads(r["prescriptions"])
    AuditRepository.log(
        action="VIEW",
        target_table="Medical_Records",
        user_id=current_user.user_id,
        details={"view": "pharmacist_prescriptions"},
    )
    return records


@router.get("/records/{record_id}")
async def get_record_pharmacist_view(
    record_id: int,
    current_user: Annotated[CurrentUser, Depends(require_pharmacist)],
):
    """
    Pharmacist view of a single record — diagnosis and notes are NOT returned.
    This is enforced at the SQL query level in the repository.
    """
    record = MedicalRecordRepository.get_pharmacist_view(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.get("prescriptions") and isinstance(record["prescriptions"], str):
        record["prescriptions"] = json.loads(record["prescriptions"])
    AuditRepository.log(
        action="VIEW",
        target_table="Medical_Records",
        target_id=record_id,
        user_id=current_user.user_id,
        details={"view": "pharmacist"},
    )
    return record


# ── Dispense ───────────────────────────────────────────────────────────────────
class DispenseRequest(BaseModel):
    record_id: int
    inventory_id: int
    quantity: int = Field(..., gt=0)
    appointment_id: int


@router.post("/dispense")
async def dispense_medication(
    body: DispenseRequest,
    current_user: Annotated[CurrentUser, Depends(require_pharmacist)],
):
    """
    Dispense medication: deduct stock + update invoice. Transactional.
    """
    invoice = BillingService.dispense_and_bill(
        record_id=body.record_id,
        inventory_id=body.inventory_id,
        quantity=body.quantity,
        dispensed_by_user_id=current_user.user_id,
        appointment_id=body.appointment_id,
    )
    return {"status": "dispensed", "invoice": invoice}


# ── Inventory lookup ───────────────────────────────────────────────────────────
@router.get("/inventory")
async def get_inventory(
    current_user: Annotated[CurrentUser, Depends(require_pharmacist)],
):
    return InventoryRepository.get_all()


@router.get("/inventory/search")
async def search_inventory(
    q: str,
    current_user: Annotated[CurrentUser, Depends(require_pharmacist)],
):
    return InventoryRepository.search(q)


@router.get("/inventory/low-stock")
async def low_stock_alert(
    current_user: Annotated[CurrentUser, Depends(require_pharmacist)],
):
    return InventoryRepository.get_low_stock()
