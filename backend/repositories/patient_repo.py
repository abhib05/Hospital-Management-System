"""
patient_repo.py – Repository for Patients table. Parameterised queries only.
"""
import json
from typing import Optional
from backend.database import execute_query, get_db_connection


class PatientRepository:

    @staticmethod
    def get_by_id(patient_id: int) -> Optional[dict]:
        sql = """
            SELECT p.*, u.username, u.role
            FROM Patients p
            JOIN Users u ON p.user_id = u.id
            WHERE p.id = %s AND p.deleted_at IS NULL
            LIMIT 1
        """
        return execute_query(sql, (patient_id,), fetch_one=True)

    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[dict]:
        sql = """
            SELECT * FROM Patients
            WHERE user_id = %s AND deleted_at IS NULL
            LIMIT 1
        """
        return execute_query(sql, (user_id,), fetch_one=True)

    @staticmethod
    def create(
        user_id: int,
        full_name: str,
        dob: str,
        gender: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        blood_group: Optional[str] = None,
        medical_history: Optional[dict] = None,
    ) -> int:
        sql = """
            INSERT INTO Patients
                (user_id, full_name, dob, gender, phone, address, blood_group, medical_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_query(
            sql,
            (
                user_id, full_name, dob, gender, phone, address,
                blood_group,
                json.dumps(medical_history) if medical_history else None,
            ),
            last_row_id=True,
        )

    @staticmethod
    def update_medical_history(patient_id: int, medical_history: dict) -> None:
        sql = """
            UPDATE Patients
            SET medical_history = %s
            WHERE id = %s AND deleted_at IS NULL
        """
        execute_query(sql, (json.dumps(medical_history), patient_id))

    @staticmethod
    def soft_delete(patient_id: int) -> None:
        sql = """
            UPDATE Patients
            SET deleted_at = NOW(), is_active = FALSE
            WHERE id = %s
        """
        execute_query(sql, (patient_id,))

    @staticmethod
    def list_patients(search: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
        if search:
            sql = """
                SELECT p.id, p.full_name, p.dob, p.gender, p.phone, p.blood_group, p.is_active
                FROM Patients p
                WHERE p.deleted_at IS NULL
                  AND (p.full_name LIKE %s OR p.phone LIKE %s)
                ORDER BY p.full_name
                LIMIT %s OFFSET %s
            """
            like = f"%{search}%"
            params = (like, like, limit, offset)
        else:
            sql = """
                SELECT p.id, p.full_name, p.dob, p.gender, p.phone, p.blood_group, p.is_active
                FROM Patients p
                WHERE p.deleted_at IS NULL
                ORDER BY p.full_name
                LIMIT %s OFFSET %s
            """
            params = (limit, offset)
        return execute_query(sql, params, fetch_all=True) or []
