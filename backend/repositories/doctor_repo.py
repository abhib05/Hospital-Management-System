"""
doctor_repo.py – Repository for Doctors table. Parameterised queries only.
"""
from typing import Optional
from backend.database import execute_query


class DoctorRepository:

    @staticmethod
    def get_by_id(doctor_id: int) -> Optional[dict]:
        sql = """
            SELECT d.*, u.username
            FROM Doctors d
            JOIN Users u ON d.user_id = u.id
            WHERE d.id = %s AND d.deleted_at IS NULL
            LIMIT 1
        """
        return execute_query(sql, (doctor_id,), fetch_one=True)

    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[dict]:
        sql = """
            SELECT * FROM Doctors
            WHERE user_id = %s AND deleted_at IS NULL
            LIMIT 1
        """
        return execute_query(sql, (user_id,), fetch_one=True)

    @staticmethod
    def create(
        user_id: int,
        full_name: str,
        specialization: str,
        fees: float,
        phone: Optional[str] = None,
    ) -> int:
        sql = """
            INSERT INTO Doctors (user_id, full_name, specialization, fees, phone)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_query(sql, (user_id, full_name, specialization, fees, phone), last_row_id=True)

    @staticmethod
    def list_doctors(specialization: Optional[str] = None) -> list[dict]:
        if specialization:
            sql = """
                SELECT d.id, d.full_name, d.specialization, d.fees, d.phone, d.is_active
                FROM Doctors d
                WHERE d.deleted_at IS NULL AND d.specialization = %s
                ORDER BY d.full_name
            """
            return execute_query(sql, (specialization,), fetch_all=True) or []
        sql = """
            SELECT d.id, d.full_name, d.specialization, d.fees, d.phone, d.is_active
            FROM Doctors d
            WHERE d.deleted_at IS NULL
            ORDER BY d.full_name
        """
        return execute_query(sql, fetch_all=True) or []

    @staticmethod
    def soft_delete(doctor_id: int) -> None:
        sql = """
            UPDATE Doctors
            SET deleted_at = NOW(), is_active = FALSE
            WHERE id = %s
        """
        execute_query(sql, (doctor_id,))
