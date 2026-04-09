from backend.auth.jwt_handler import verify_password
import sys

hashed = "$2b$12$KIX9U8vhbJ1JQcT6Y2fMKeoFb4QzHYyGpF3HFe3z1PRMm5Mxd.EwC"
valid = verify_password('Password123!', hashed)
print(f"IS VALID: {valid}")
