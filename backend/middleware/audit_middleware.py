"""
audit_middleware.py – FastAPI middleware that logs every incoming request
to the Audit_Logs table (fire-and-forget, never blocks response).

Sensitive endpoints (medical records, auth) are tagged explicitly.
"""
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.repositories.audit_repo import AuditRepository

logger = logging.getLogger(__name__)

# Map URL prefixes → (action, target_table) for semantic logging
_ROUTE_MAP = {
    "/api/medical-records":  ("VIEW",   "Medical_Records"),
    "/api/appointments":     ("VIEW",   "Appointments"),
    "/api/patients":         ("VIEW",   "Patients"),
    "/api/doctors":          ("VIEW",   "Doctors"),
    "/api/inventory":        ("VIEW",   "Inventory"),
    "/api/invoices":         ("VIEW",   "Invoices"),
    "/api/auth/login":       ("LOGIN",  "Users"),
    "/api/transcribe":       ("CREATE", "Medical_Records"),
    "/api/dispense":         ("DISPENSE","Dispensed_Items"),
}

# Write methods upgrade action to CREATE/UPDATE/DELETE
_METHOD_ACTION = {
    "POST":   "CREATE",
    "PUT":    "UPDATE",
    "PATCH":  "UPDATE",
    "DELETE": "DELETE",
}


class AuditMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Only log API routes
        path = request.url.path
        if not path.startswith("/api/"):
            return response

        # Determine action + table
        action = _METHOD_ACTION.get(request.method.upper(), "VIEW")
        target_table = "API"
        for prefix, (default_action, table) in _ROUTE_MAP.items():
            if path.startswith(prefix):
                target_table = table
                if action == "VIEW":         # GET stays as VIEW
                    action = default_action
                break

        # Get user from request state (set by RBAC dependency)
        user = getattr(getattr(request, "state", None), "current_user", None)
        user_id = user.user_id if user else None

        ip = request.client.host if request.client else None

        AuditRepository.log(
            action=action,
            target_table=target_table,
            user_id=user_id,
            ip_address=ip,
            details={
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 1),
            },
        )
        return response
