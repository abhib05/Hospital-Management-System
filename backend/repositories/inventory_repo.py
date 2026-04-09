"""
inventory_repo.py – Repository for Inventory and Dispensed_Items tables.
"""
from typing import Optional
from backend.database import execute_query, get_db_connection


class InventoryRepository:

    @staticmethod
    def get_all(include_inactive: bool = False) -> list[dict]:
        if include_inactive:
            sql = "SELECT * FROM Inventory ORDER BY drug_name"
        else:
            sql = "SELECT * FROM Inventory WHERE is_active = TRUE ORDER BY drug_name"
        return execute_query(sql, fetch_all=True) or []

    @staticmethod
    def get_by_id(inventory_id: int) -> Optional[dict]:
        sql = "SELECT * FROM Inventory WHERE id = %s LIMIT 1"
        return execute_query(sql, (inventory_id,), fetch_one=True)

    @staticmethod
    def search(query: str) -> list[dict]:
        sql = """
            SELECT * FROM Inventory
            WHERE is_active = TRUE
              AND (drug_name LIKE %s OR generic_name LIKE %s)
            ORDER BY drug_name
            LIMIT 20
        """
        like = f"%{query}%"
        return execute_query(sql, (like, like), fetch_all=True) or []

    @staticmethod
    def deduct_stock(inventory_id: int, quantity: int, conn=None) -> bool:
        """
        Atomically deduct stock. Returns False if insufficient stock.
        Must be called within a transaction for safety.
        """
        check_sql = """
            SELECT stock_qty FROM Inventory
            WHERE id = %s AND is_active = TRUE
            FOR UPDATE
        """
        update_sql = """
            UPDATE Inventory
            SET stock_qty = stock_qty - %s
            WHERE id = %s AND stock_qty >= %s
        """
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(check_sql, (inventory_id,))
            row = cursor.fetchone()
            if not row or row["stock_qty"] < quantity:
                return False
            cursor.execute(update_sql, (quantity, inventory_id, quantity))
            return cursor.rowcount > 0
        else:
            with get_db_connection() as c:
                cursor = c.cursor(dictionary=True)
                cursor.execute(check_sql, (inventory_id,))
                row = cursor.fetchone()
                if not row or row["stock_qty"] < quantity:
                    return False
                cursor.execute(update_sql, (quantity, inventory_id, quantity))
                return cursor.rowcount > 0

    @staticmethod
    def record_dispense(
        record_id: int,
        inventory_id: int,
        quantity: int,
        dispensed_by: int,
        conn=None,
    ) -> int:
        sql = """
            INSERT INTO Dispensed_Items
                (record_id, inventory_id, quantity, dispensed_by)
            VALUES (%s, %s, %s, %s)
        """
        return execute_query(
            sql, (record_id, inventory_id, quantity, dispensed_by),
            last_row_id=True, conn=conn
        )

    @staticmethod
    def get_dispensed_by_record(record_id: int) -> list[dict]:
        sql = """
            SELECT di.*, i.drug_name, i.unit, i.unit_price,
                   (di.quantity * i.unit_price) AS line_total
            FROM Dispensed_Items di
            JOIN Inventory i ON di.inventory_id = i.id
            WHERE di.record_id = %s
        """
        return execute_query(sql, (record_id,), fetch_all=True) or []

    @staticmethod
    def get_low_stock(threshold: Optional[int] = None) -> list[dict]:
        sql = """
            SELECT * FROM Inventory
            WHERE is_active = TRUE AND stock_qty <= reorder_level
            ORDER BY stock_qty ASC
        """
        return execute_query(sql, fetch_all=True) or []
