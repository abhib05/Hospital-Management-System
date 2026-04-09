-- ============================================================
-- Hospital Management System (HMS) - MySQL Schema
-- ============================================================
-- Encoding: UTF-8 | Engine: InnoDB | Charset: utf8mb4

CREATE DATABASE IF NOT EXISTS hms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hms_db;

-- ──────────────────────────────────────────────
-- 1. USERS  (auth identity + role hub)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Users (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('Admin','Doctor','Patient','Pharmacist','LabTech') NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at    DATETIME     NULL DEFAULT NULL,       -- soft-delete
    INDEX idx_users_role (role),
    INDEX idx_users_active (is_active)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 2. DOCTORS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Doctors (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL UNIQUE,
    full_name       VARCHAR(120) NOT NULL,
    specialization  VARCHAR(100) NOT NULL,
    fees            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    phone           VARCHAR(20)  NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted_at      DATETIME     NULL DEFAULT NULL,     -- soft-delete
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_doctors_user FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE RESTRICT,
    INDEX idx_doctors_user (user_id)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 3. PATIENTS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Patients (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL UNIQUE,
    full_name       VARCHAR(120) NOT NULL,
    dob             DATE         NOT NULL,
    gender          ENUM('Male','Female','Other') NOT NULL,
    phone           VARCHAR(20)  NULL,
    address         TEXT         NULL,
    blood_group     VARCHAR(5)   NULL,
    medical_history JSON         NULL,                  -- JSON column
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted_at      DATETIME     NULL DEFAULT NULL,     -- soft-delete
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_patients_user FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE RESTRICT,
    INDEX idx_patients_user (user_id)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 4. APPOINTMENTS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Appointments (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT UNSIGNED NOT NULL,
    doctor_id       INT UNSIGNED NOT NULL,
    scheduled_at    DATETIME     NOT NULL,
    status          ENUM('Scheduled','Completed','No-Show','Cancelled') NOT NULL DEFAULT 'Scheduled',
    reason          TEXT         NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_appt_patient FOREIGN KEY (patient_id) REFERENCES Patients(id) ON DELETE RESTRICT,
    CONSTRAINT fk_appt_doctor  FOREIGN KEY (doctor_id)  REFERENCES Doctors(id)  ON DELETE RESTRICT,
    INDEX idx_appt_doctor_status  (doctor_id, status),
    INDEX idx_appt_patient        (patient_id),
    INDEX idx_appt_scheduled_at   (scheduled_at)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 5. MEDICAL RECORDS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Medical_Records (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    appointment_id  INT UNSIGNED NOT NULL UNIQUE,
    patient_id      INT UNSIGNED NOT NULL,
    doctor_id       INT UNSIGNED NOT NULL,
    diagnosis       TEXT         NULL,                  -- restricted from Pharmacist
    notes           TEXT         NULL,                  -- AI-transcribed + doctor edits; restricted from Pharmacist
    prescriptions   JSON         NOT NULL DEFAULT (JSON_ARRAY()),  -- JSON column
    lab_results     JSON         NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_mr_appointment FOREIGN KEY (appointment_id) REFERENCES Appointments(id) ON DELETE RESTRICT,
    CONSTRAINT fk_mr_patient     FOREIGN KEY (patient_id)     REFERENCES Patients(id)     ON DELETE RESTRICT,
    CONSTRAINT fk_mr_doctor      FOREIGN KEY (doctor_id)      REFERENCES Doctors(id)      ON DELETE RESTRICT,
    INDEX idx_mr_patient (patient_id),
    INDEX idx_mr_doctor  (doctor_id)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 6. INVENTORY  (pharmacy drug stock)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Inventory (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    drug_name       VARCHAR(150) NOT NULL,
    generic_name    VARCHAR(150) NULL,
    unit            VARCHAR(30)  NOT NULL DEFAULT 'tablet',
    unit_price      DECIMAL(10,2) NOT NULL,
    stock_qty       INT          NOT NULL DEFAULT 0,
    reorder_level   INT          NOT NULL DEFAULT 10,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_inv_drug_name (drug_name)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 7. DISPENSED ITEMS  (pharmacist marks as dispensed)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Dispensed_Items (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    record_id       INT UNSIGNED NOT NULL,
    inventory_id    INT UNSIGNED NOT NULL,
    quantity        INT          NOT NULL,
    dispensed_by    INT UNSIGNED NOT NULL,             -- FK → Users.id (Pharmacist)
    dispensed_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_di_record     FOREIGN KEY (record_id)     REFERENCES Medical_Records(id) ON DELETE RESTRICT,
    CONSTRAINT fk_di_inventory  FOREIGN KEY (inventory_id)  REFERENCES Inventory(id)       ON DELETE RESTRICT,
    CONSTRAINT fk_di_pharmacist FOREIGN KEY (dispensed_by)  REFERENCES Users(id)           ON DELETE RESTRICT,
    INDEX idx_di_record (record_id)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 8. INVOICES
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Invoices (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT UNSIGNED NOT NULL,
    appointment_id  INT UNSIGNED NOT NULL UNIQUE,
    consultation_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    pharmacy_total  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    grand_total     DECIMAL(10,2) GENERATED ALWAYS AS (consultation_fee + pharmacy_total) STORED,
    payment_status  ENUM('Pending','Paid','Waived') NOT NULL DEFAULT 'Pending',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_inv_patient     FOREIGN KEY (patient_id)     REFERENCES Patients(id)     ON DELETE RESTRICT,
    CONSTRAINT fk_inv_appointment FOREIGN KEY (appointment_id) REFERENCES Appointments(id) ON DELETE RESTRICT,
    INDEX idx_inv_patient (patient_id),
    INDEX idx_inv_payment (payment_status)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 9. AUDIT LOGS  (every DB read/write on sensitive data)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Audit_Logs (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NULL,                  -- NULL if system action
    action          ENUM('VIEW','CREATE','UPDATE','DELETE','LOGIN','LOGOUT','DISPENSE') NOT NULL,
    target_table    VARCHAR(60)  NOT NULL,
    target_id       INT UNSIGNED NULL,
    details         TEXT         NULL,                  -- JSON-encoded extra context
    ip_address      VARCHAR(45)  NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE SET NULL,
    INDEX idx_audit_user   (user_id),
    INDEX idx_audit_table  (target_table),
    INDEX idx_audit_action (action),
    INDEX idx_audit_ts     (created_at)
) ENGINE=InnoDB;

-- ──────────────────────────────────────────────
-- 10. LAB TESTS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Lab_Tests (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    record_id       INT UNSIGNED NOT NULL,
    test_name       VARCHAR(150) NOT NULL,
    ordered_by      INT UNSIGNED NOT NULL,             -- FK → Doctors.id
    assigned_to     INT UNSIGNED NULL,                 -- FK → Users.id (LabTech)
    status          ENUM('Ordered','In-Progress','Completed') NOT NULL DEFAULT 'Ordered',
    result_notes    TEXT         NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_lt_record  FOREIGN KEY (record_id)  REFERENCES Medical_Records(id) ON DELETE RESTRICT,
    CONSTRAINT fk_lt_doctor  FOREIGN KEY (ordered_by) REFERENCES Doctors(id)         ON DELETE RESTRICT,
    CONSTRAINT fk_lt_tech    FOREIGN KEY (assigned_to) REFERENCES Users(id)          ON DELETE SET NULL,
    INDEX idx_lt_record (record_id),
    INDEX idx_lt_status (status)
) ENGINE=InnoDB;
