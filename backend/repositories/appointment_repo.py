"""
appointment_repo.py – Repository for Appointments table.
Implements transaction-safe booking to prevent double-booking.
"""
from typing import Optional
from datetime import datetime

from backend.database import execute_query, get_db_connection


class AppointmentRepository:

    @staticmethod
    def book_appointment(
        patient_id: int,
        doctor_id: int,
        scheduled_at: datetime,
        reason: Optional[str] = None,
    ) -> int:
        """
        Book an appointment inside a single transaction.
        Locks the doctor's slot to prevent double-booking (SELECT ... FOR UPDATE).
        Returns the new appointment id.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Lock any conflicting appointment for this doctor in a ±30-min window
            cursor.execute(
                """
                SELECT id FROM Appointments
                WHERE doctor_id = %s
                  AND status = 'Scheduled'
                  AND scheduled_at BETWEEN
                      DATE_SUB(%s, INTERVAL 29 MINUTE) AND
                      DATE_ADD(%s, INTERVAL 29 MINUTE)
                FOR UPDATE
                """,
                (doctor_id, scheduled_at, scheduled_at),
            )
            conflict = cursor.fetchone()
            if conflict:
                conn.rollback()
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Doctor already has an appointment within ±30 minutes of that time.",
                )

            cursor.execute(
                """
                INSERT INTO Appointments (patient_id, doctor_id, scheduled_at, reason)
                VALUES (%s, %s, %s, %s)
                """,
                (patient_id, doctor_id, scheduled_at, reason),
            )
            new_id = cursor.lastrowid
            conn.commit()
            return new_id

    @staticmethod
    def get_by_id(appointment_id: int) -> Optional[dict]:
        sql = """
            SELECT a.*,
                   p.full_name AS patient_name,
                   d.full_name AS doctor_name,
                   d.specialization, d.fees
            FROM Appointments a
            JOIN Patients p ON a.patient_id = p.id
            JOIN Doctors  d ON a.doctor_id  = d.id
            WHERE a.id = %s
            LIMIT 1
        """
        return execute_query(sql, (appointment_id,), fetch_one=True)

    @staticmethod
    def get_doctor_appointments(
        doctor_id: int,
        status: Optional[str] = None,
        date: Optional[str] = None,
    ) -> list[dict]:
        conditions = ["a.doctor_id = %s"]
        params: list = [doctor_id]

        if status:
            conditions.append("a.status = %s")
            params.append(status)
        if date:
            conditions.append("DATE(a.scheduled_at) = %s")
            params.append(date)

        sql = f"""
            SELECT a.id, a.scheduled_at, a.status, a.reason,
                   p.full_name AS patient_name, p.id AS patient_id
            FROM Appointments a
            JOIN Patients p ON a.patient_id = p.id
            WHERE {' AND '.join(conditions)}
            ORDER BY a.scheduled_at ASC
        """
        return execute_query(sql, tuple(params), fetch_all=True) or []

    @staticmethod
    def get_patient_appointments(patient_id: int) -> list[dict]:
        sql = """
            SELECT a.id, a.scheduled_at, a.status, a.reason,
                   d.full_name AS doctor_name, d.specialization
            FROM Appointments a
            JOIN Doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = %s
            ORDER BY a.scheduled_at DESC
        """
        return execute_query(sql, (patient_id,), fetch_all=True) or []

    @staticmethod
    def update_status(appointment_id: int, new_status: str) -> None:
        sql = """
            UPDATE Appointments SET status = %s WHERE id = %s
        """
        execute_query(sql, (new_status, appointment_id))

    @staticmethod
    def count_scheduled_this_hour(doctor_id: int) -> int:
        sql = """
            SELECT COUNT(*) AS cnt
            FROM Appointments
            WHERE doctor_id = %s
              AND status = 'Scheduled'
              AND scheduled_at BETWEEN
                  DATE_FORMAT(NOW(), '%Y-%m-%d %H:00:00') AND
                  DATE_FORMAT(NOW(), '%Y-%m-%d %H:59:59')
        """
        row = execute_query(sql, (doctor_id,), fetch_one=True)
        return row["cnt"] if row else 0
