"""
billing_service.py – Business logic for billing and invoice generation.
Calculates: consultation_fee + sum(dispensed items × unit_price).
"""
from fastapi import HTTPException, status

from backend.repositories.invoice_repo import InvoiceRepository
from backend.repositories.inventory_repo import InventoryRepository
from backend.repositories.appointment_repo import AppointmentRepository
from backend.repositories.doctor_repo import DoctorRepository
from backend.repositories.audit_repo import AuditRepository
from backend.database import get_db_connection


class BillingService:

    @staticmethod
    def generate_invoice(appointment_id: int, actor_user_id: int) -> dict:
        """
        Create an invoice for a completed appointment.
        consultation_fee is pulled from the doctor's fee schedule.
        """
        appt = AppointmentRepository.get_by_id(appointment_id)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        # Check no existing invoice
        existing = InvoiceRepository.get_by_appointment(appointment_id)
        if existing:
            return existing

        invoice_id = InvoiceRepository.create(
            patient_id=appt["patient_id"],
            appointment_id=appointment_id,
            consultation_fee=float(appt["fees"]),
        )
        AuditRepository.log(
            action="CREATE",
            target_table="Invoices",
            target_id=invoice_id,
            user_id=actor_user_id,
            details={"appointment_id": appointment_id, "consultation_fee": float(appt["fees"])},
        )
        return InvoiceRepository.get_by_appointment(appointment_id)

    @staticmethod
    def dispense_and_bill(
        record_id: int,
        inventory_id: int,
        quantity: int,
        dispensed_by_user_id: int,
        appointment_id: int,
    ) -> dict:
        """
        Transactional dispense:
        1. Lock and deduct stock.
        2. Record the Dispensed_Item.
        3. Recalculate and update pharmacy_total on the Invoice.
        Returns updated invoice.
        """
        with get_db_connection() as conn:
            # 1. Deduct stock (FOR UPDATE lock inside)
            success = InventoryRepository.deduct_stock(inventory_id, quantity, conn=conn)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Insufficient stock for the requested quantity.",
                )
            # 2. Record dispense
            InventoryRepository.record_dispense(
                record_id, inventory_id, quantity, dispensed_by_user_id, conn=conn
            )
            conn.commit()

        # 3. Recalculate pharmacy total
        dispensed = InventoryRepository.get_dispensed_by_record(record_id)
        pharmacy_total = sum(float(item["line_total"]) for item in dispensed)
        InvoiceRepository.update_pharmacy_total(appointment_id, pharmacy_total)

        AuditRepository.log(
            action="DISPENSE",
            target_table="Dispensed_Items",
            target_id=record_id,
            user_id=dispensed_by_user_id,
            details={
                "inventory_id": inventory_id,
                "quantity": quantity,
                "pharmacy_total": pharmacy_total,
            },
        )
        return InvoiceRepository.get_by_appointment(appointment_id)

    @staticmethod
    def get_invoice_detail(appointment_id: int) -> dict:
        invoice = InvoiceRepository.get_by_appointment(appointment_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice
