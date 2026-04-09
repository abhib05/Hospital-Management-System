"""
invoice_repo.py – Repository for Invoices table.
"""
from typing import Optional
from backend.database import execute_query, get_db_connection


class InvoiceRepository:

    @staticmethod
    def create(patient_id: int, appointment_id: int, consultation_fee: float) -> int:
        sql = """
            INSERT INTO Invoices (patient_id, appointment_id, consultation_fee)
            VALUES (%s, %s, %s)
        """
        return execute_query(
            sql, (patient_id, appointment_id, consultation_fee), last_row_id=True
        )

    @staticmethod
    def get_by_appointment(appointment_id: int) -> Optional[dict]:
        sql = """
            SELECT inv.*, p.full_name AS patient_name
            FROM Invoices inv
            JOIN Patients p ON inv.patient_id = p.id
            WHERE inv.appointment_id = %s
            LIMIT 1
        """
        return execute_query(sql, (appointment_id,), fetch_one=True)

    @staticmethod
    def update_pharmacy_total(appointment_id: int, pharmacy_total: float) -> None:
        sql = """
            UPDATE Invoices
            SET pharmacy_total = %s
            WHERE appointment_id = %s
        """
        execute_query(sql, (pharmacy_total, appointment_id))

    @staticmethod
    def mark_paid(invoice_id: int) -> None:
        sql = "UPDATE Invoices SET payment_status = 'Paid' WHERE id = %s"
        execute_query(sql, (invoice_id,))

    @staticmethod
    def get_patient_invoices(patient_id: int) -> list[dict]:
        sql = """
            SELECT inv.*, a.scheduled_at, d.full_name AS doctor_name
            FROM Invoices inv
            JOIN Appointments a ON inv.appointment_id = a.id
            JOIN Doctors      d ON a.doctor_id        = d.id
            WHERE inv.patient_id = %s
            ORDER BY inv.created_at DESC
        """
        return execute_query(sql, (patient_id,), fetch_all=True) or []
