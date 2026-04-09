"""
medical_record_repo.py – Repository for Medical_Records table.
Privacy note:
  - Full records (including diagnosis/notes) returned only for Doctors / Admin.
  - Pharmacist queries EXCLUDE diagnosis and notes at the SQL level.
"""
import json
from typing import Optional
from backend.database import execute_query


class MedicalRecordRepository:

    @staticmethod
    def create(appointment_id: int, patient_id: int, doctor_id: int) -> int:
        sql = """
            INSERT INTO Medical_Records
                (appointment_id, patient_id, doctor_id, prescriptions)
            VALUES (%s, %s, %s, JSON_ARRAY())
        """
        return execute_query(
            sql, (appointment_id, patient_id, doctor_id), last_row_id=True
        )

    @staticmethod
    def get_full(record_id: int) -> Optional[dict]:
        """Full record for Doctor / Admin — includes diagnosis and notes."""
        sql = """
            SELECT mr.*,
                   p.full_name AS patient_name,
                   d.full_name AS doctor_name
            FROM Medical_Records mr
            JOIN Patients p ON mr.patient_id = p.id
            JOIN Doctors  d ON mr.doctor_id  = d.id
            WHERE mr.id = %s
            LIMIT 1
        """
        return execute_query(sql, (record_id,), fetch_one=True)

    @staticmethod
    def get_pharmacist_view(record_id: int) -> Optional[dict]:
        """
        Pharmacist view — diagnosis and notes are EXCLUDED at query level,
        not just hidden in the frontend. Access control is enforced here.
        """
        sql = """
            SELECT mr.id,
                   mr.appointment_id,
                   mr.patient_id,
                   mr.prescriptions,
                   mr.created_at,
                   mr.updated_at,
                   p.full_name AS patient_name
            FROM Medical_Records mr
            JOIN Patients p ON mr.patient_id = p.id
            WHERE mr.id = %s
            LIMIT 1
        """
        return execute_query(sql, (record_id,), fetch_one=True)

    @staticmethod
    def update_notes_and_diagnosis(
        record_id: int,
        notes: Optional[str] = None,
        diagnosis: Optional[str] = None,
    ) -> None:
        updates = []
        params = []
        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)
        if diagnosis is not None:
            updates.append("diagnosis = %s")
            params.append(diagnosis)
        if not updates:
            return
        params.append(record_id)
        sql = f"UPDATE Medical_Records SET {', '.join(updates)} WHERE id = %s"
        execute_query(sql, tuple(params))

    @staticmethod
    def update_prescriptions(record_id: int, prescriptions: list) -> None:
        sql = """
            UPDATE Medical_Records
            SET prescriptions = %s
            WHERE id = %s
        """
        execute_query(sql, (json.dumps(prescriptions), record_id))

    @staticmethod
    def get_by_patient(patient_id: int, limit: int = 20) -> list[dict]:
        """Full history for the doctor / admin view."""
        sql = """
            SELECT mr.id, mr.diagnosis, mr.notes, mr.prescriptions,
                   mr.created_at, d.full_name AS doctor_name,
                   a.scheduled_at
            FROM Medical_Records mr
            JOIN Doctors d      ON mr.doctor_id      = d.id
            JOIN Appointments a ON mr.appointment_id = a.id
            WHERE mr.patient_id = %s
            ORDER BY mr.created_at DESC
            LIMIT %s
        """
        return execute_query(sql, (patient_id, limit), fetch_all=True) or []

    @staticmethod
    def get_pending_dispense(doctor_id: Optional[int] = None) -> list[dict]:
        """Records with prescriptions that haven't been fully dispensed."""
        if doctor_id:
            sql = """
                SELECT mr.id, mr.prescriptions, mr.patient_id,
                       p.full_name AS patient_name, a.scheduled_at
                FROM Medical_Records mr
                JOIN Patients p      ON mr.patient_id      = p.id
                JOIN Appointments a  ON mr.appointment_id  = a.id
                WHERE mr.doctor_id = %s
                  AND JSON_LENGTH(mr.prescriptions) > 0
                ORDER BY mr.created_at DESC
                LIMIT 50
            """
            return execute_query(sql, (doctor_id,), fetch_all=True) or []
        sql = """
            SELECT mr.id, mr.prescriptions, mr.patient_id,
                   p.full_name AS patient_name, a.scheduled_at
            FROM Medical_Records mr
            JOIN Patients p     ON mr.patient_id     = p.id
            JOIN Appointments a ON mr.appointment_id = a.id
            WHERE JSON_LENGTH(mr.prescriptions) > 0
            ORDER BY mr.created_at DESC
            LIMIT 100
        """
        return execute_query(sql, fetch_all=True) or []
