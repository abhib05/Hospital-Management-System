"""
audit_repo.py – Repository for Audit_Logs table.
All queries are strictly parameterised.
"""
import json
import logging
from typing import Optional

from backend.database import execute_query, get_db_connection

logger = logging.getLogger(__name__)


class AuditRepository:

    @staticmethod
    def log(
        action: str,
        target_table: str,
        target_id: Optional[int] = None,
        user_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        conn=None,
    ) -> None:
        """
        Insert one audit log entry. Fire-and-forget (exceptions are caught+logged,
        never bubble up to the caller so they don't break the main request).
        """
        sql = """
            INSERT INTO Audit_Logs
                (user_id, action, target_table, target_id, details, ip_address)
            VALUES
                (%s, %s, %s, %s, %s, %s)
        """
        params = (
            user_id,
            action,
            target_table,
            target_id,
            json.dumps(details) if details else None,
            ip_address,
        )
        try:
            execute_query(sql, params, conn=conn)
        except Exception as exc:
            # Audit failures must never crash the main request
            logger.error("Audit log write failed: %s", exc)

    @staticmethod
    def get_logs(
        user_id: Optional[int] = None,
        target_table: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        conditions = ["1=1"]
        params: list = []

        if user_id is not None:
            conditions.append("user_id = %s")
            params.append(user_id)
        if target_table:
            conditions.append("target_table = %s")
            params.append(target_table)
        if action:
            conditions.append("action = %s")
            params.append(action)

        sql = f"""
            SELECT al.*, u.username
            FROM Audit_Logs al
            LEFT JOIN Users u ON al.user_id = u.id
            WHERE {' AND '.join(conditions)}
            ORDER BY al.created_at DESC
            LIMIT %s OFFSET %s
        """
        params += [limit, offset]
        return execute_query(sql, tuple(params), fetch_all=True) or []
