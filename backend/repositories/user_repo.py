"""
user_repo.py – Repository for Users table. Parameterised queries only.
"""
from typing import Optional
from backend.database import execute_query


class UserRepository:

    @staticmethod
    def get_by_username(username: str) -> Optional[dict]:
        sql = """
            SELECT id, username, password_hash, role, is_active
            FROM Users
            WHERE username = %s AND deleted_at IS NULL
            LIMIT 1
        """
        return execute_query(sql, (username,), fetch_one=True)

    @staticmethod
    def get_by_id(user_id: int) -> Optional[dict]:
        sql = """
            SELECT id, username, role, is_active, created_at
            FROM Users
            WHERE id = %s AND deleted_at IS NULL
            LIMIT 1
        """
        return execute_query(sql, (user_id,), fetch_one=True)

    @staticmethod
    def create(username: str, password_hash: str, role: str) -> int:
        sql = """
            INSERT INTO Users (username, password_hash, role)
            VALUES (%s, %s, %s)
        """
        return execute_query(sql, (username, password_hash, role), last_row_id=True)

    @staticmethod
    def soft_delete(user_id: int) -> None:
        sql = """
            UPDATE Users
            SET deleted_at = NOW(), is_active = FALSE
            WHERE id = %s
        """
        execute_query(sql, (user_id,))

    @staticmethod
    def list_users(role: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
        if role:
            sql = """
                SELECT id, username, role, is_active, created_at
                FROM Users
                WHERE role = %s AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (role, limit, offset)
        else:
            sql = """
                SELECT id, username, role, is_active, created_at
                FROM Users
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (limit, offset)
        return execute_query(sql, params, fetch_all=True) or []
