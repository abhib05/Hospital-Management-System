# Hospital Management System (HMS)

A full-featured, production-ready HMS built with **FastAPI**, **MySQL**, and vanilla **HTML/Tailwind CSS**. Includes AI-powered voice transcription using `faster-whisper` optimised for CPU-only inference.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| Database | MySQL 8.0+ (`mysql-connector-python`) |
| AI Engine | `faster-whisper` (`distil-large-v3`, `int8` CPU) |
| Auth | JWT (python-jose) · bcrypt passwords |
| Frontend | HTML5 · Tailwind CSS (CDN) · Vanilla JS |
| Audio | MediaRecorder API → `.webm` → `ffmpeg` normalise → Whisper |

---

## Quick Start

### 1. Prerequisites

```bash
# System dependencies
sudo apt install ffmpeg mysql-server   # Ubuntu/Debian
# or: brew install ffmpeg mysql        # macOS

# Python 3.11+
python3 --version
```

### 2. Clone & Install

```bash
cd DBS_PROJECT_PYTHON_2.0
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt --break-system-packages
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env — set DB_PASSWORD, JWT_SECRET_KEY, etc.
nano .env
```

### 4. Set Up Database

```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create user and grant permissions
CREATE USER 'hms_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON hms_db.* TO 'hms_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# Run schema + seed data
mysql -u hms_user -p hms_db < database/schema.sql
mysql -u hms_user -p hms_db < database/seed_data.sql
```

### 5. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser: **http://localhost:8000**

---

## Architecture

```
DBS_PROJECT_PYTHON_2.0/
├── main.py                          # FastAPI app entry point + lifespan
├── requirements.txt
├── .env.example
├── database/
│   ├── schema.sql                   # All CREATE TABLE scripts (10 tables)
│   └── seed_data.sql                # Demo data
├── backend/
│   ├── config.py                    # Pydantic Settings (reads .env)
│   ├── database.py                  # MySQL connection pool + parameterised queries
│   ├── auth/
│   │   ├── jwt_handler.py           # JWT create/decode + bcrypt
│   │   └── rbac.py                  # FastAPI Depends() guards per role
│   ├── repositories/                # RAW MySQL queries — SQL layer
│   │   ├── user_repo.py
│   │   ├── patient_repo.py
│   │   ├── doctor_repo.py
│   │   ├── appointment_repo.py      # Double-booking prevention (SELECT FOR UPDATE)
│   │   ├── medical_record_repo.py   # Pharmacist view excludes diagnosis/notes at SQL level
│   │   ├── inventory_repo.py        # Atomic stock deduction
│   │   ├── invoice_repo.py
│   │   └── audit_repo.py
│   ├── services/                    # Business logic layer
│   │   ├── auth_service.py
│   │   ├── appointment_service.py
│   │   ├── billing_service.py       # Calculates fee + pharmacy totals
│   │   ├── transcription_service.py # faster-whisper singleton + ffmpeg normalisation
│   │   └── queue_service.py         # Wait-time estimator
│   ├── controllers/                 # FastAPI routers (API routes + validation)
│   │   ├── auth_controller.py       # POST /api/auth/login, /register
│   │   ├── doctor_controller.py     # Doctor dashboard endpoints
│   │   ├── pharmacist_controller.py # Pharmacist endpoints (restricted views)
│   │   ├── patient_controller.py    # Patient portal endpoints
│   │   ├── admin_controller.py      # Admin CRUD + audit log viewer
│   │   └── transcription_controller.py  # POST /api/transcribe
│   └── middleware/
│       └── audit_middleware.py      # Logs every API hit to Audit_Logs table
└── frontend/
    ├── index.html                   # Login page (role-based redirect)
    ├── doctor_dashboard.html        # Audio recording + transcription + prescriptions
    ├── pharmacist_dashboard.html    # Prescriptions (no diagnosis) + dispense + inventory
    ├── patient_portal.html          # Appointments booking + invoices + masked profile
    ├── admin_dashboard.html         # Users + inventory + audit logs + registration
    └── js/
        └── api.js                   # Shared: Auth, fetch wrapper, toasts, spinners
```

---

## Demo Accounts

All demo passwords: `Password123!`

| Username | Role | Dashboard |
|----------|------|-----------|
| `admin` | Admin | `/admin_dashboard.html` |
| `dr_smith` | Doctor | `/doctor_dashboard.html` |
| `dr_chen` | Doctor | `/doctor_dashboard.html` |
| `patient_john` | Patient | `/patient_portal.html` |
| `patient_mary` | Patient | `/patient_portal.html` |
| `pharmacist1` | Pharmacist | `/pharmacist_dashboard.html` |
| `labtech1` | LabTech | *(staff access)* |

---

## Key Security Features

### SQL Injection Prevention
All queries use parameterised placeholders — **zero f-strings in SQL** across the entire codebase. See `database.py → execute_query()`.

### Soft Deletes
`Patients` and `Doctors` tables include `deleted_at` and `is_active`. Records are never hard-deleted; all queries filter `WHERE deleted_at IS NULL`.

### Data Isolation (Pharmacist)
The `MedicalRecordRepository.get_pharmacist_view()` method **excludes `diagnosis` and `notes` at the SQL level**. The pharmacist never receives these columns regardless of frontend state.

### Sensitive Data Masking (Patient Portal)
Patient `phone`, `address`, and `medical_history` are masked by default on `/api/patients/me`. Calling `/api/patients/me/full` returns the unmasked data but triggers an `Audit_Log` entry.

### Double-Booking Prevention
`AppointmentRepository.book_appointment()` uses `SELECT … FOR UPDATE` inside a single transaction to lock the doctor's time slot before inserting.

### AI Singleton
The `WhisperModel` is initialised exactly once during `app lifespan` startup. All `/api/transcribe` requests reuse the same in-memory model.

### Audit Middleware
`AuditMiddleware` logs every API request to `Audit_Logs`, including the user, action, target table, HTTP status, and duration.

---

## API Reference

Interactive docs at **http://localhost:8000/api/docs** (Swagger UI).

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login → JWT |
| POST | `/api/auth/register` | Register user |

### Transcription
| Method | Path | Role |
|--------|------|------|
| POST | `/api/transcribe` | Doctor only — multipart audio |

### Doctor
| Method | Path |
|--------|------|
| GET | `/api/doctors/me` |
| GET | `/api/doctors/appointments` |
| POST | `/api/doctors/appointments/{id}/complete` |
| GET | `/api/doctors/queue` |
| GET/PATCH | `/api/doctors/records/{id}` |

### Pharmacist
| Method | Path |
|--------|------|
| GET | `/api/pharmacist/prescriptions` |
| GET | `/api/pharmacist/records/{id}` |
| POST | `/api/pharmacist/dispense` |
| GET | `/api/pharmacist/inventory` |

### Patient
| Method | Path |
|--------|------|
| GET | `/api/patients/me` |
| GET | `/api/patients/me/full` *(audit-logged)* |
| GET/POST | `/api/patients/me/appointments` |
| GET | `/api/patients/me/invoices` |

### Admin
| Method | Path |
|--------|------|
| GET | `/api/admin/users` |
| DELETE | `/api/admin/users/{id}` |
| GET | `/api/admin/audit-logs` |
| POST | `/api/admin/inventory` |
| PATCH | `/api/admin/inventory/{id}/restock` |
| POST | `/api/admin/doctors` |
| POST | `/api/admin/patients` |

---

## Environment Variables

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=hms_user
DB_PASSWORD=<strong_password>
DB_NAME=hms_db

JWT_SECRET_KEY=<32+ char random string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

WHISPER_MODEL_SIZE=distil-large-v3
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

APP_ENV=development
APP_PORT=8000

AUDIO_UPLOAD_DIR=./uploads/audio
FFMPEG_PATH=ffmpeg
```

---

## Notes on CPU Transcription

The `distil-large-v3` model with `compute_type=int8` is ~2× faster than float16 on CPU-only hardware, and the distilled model is ~250 MB. Expect 5–15 seconds transcription per minute of audio on a typical Intel i5/i7. The frontend shows a loading spinner after submitting audio to prevent duplicate submissions.
