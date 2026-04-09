-- ============================================================
-- HMS Seed Data  (for development/demo only)
-- Passwords are bcrypt hashes of "Password123!"
-- ============================================================
USE hms_db;

-- ── Users ──────────────────────────────────────────────────
INSERT INTO Users (username, password_hash, role) VALUES
  ('admin',        '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Admin'),
  ('dr_smith',     '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Doctor'),
  ('dr_chen',      '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Doctor'),
  ('patient_john', '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Patient'),
  ('patient_mary', '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Patient'),
  ('pharmacist1',  '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Pharmacist'),
  ('labtech1',     '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'LabTech');

-- ── Doctors ────────────────────────────────────────────────
INSERT INTO Doctors (user_id, full_name, specialization, fees, phone) VALUES
  (2, 'Dr. James Smith',  'General Practice', 150.00, '+1-555-0101'),
  (3, 'Dr. Li Chen',      'Cardiology',       250.00, '+1-555-0102');

-- ── Patients ───────────────────────────────────────────────
INSERT INTO Patients (user_id, full_name, dob, gender, phone, blood_group, medical_history) VALUES
  (4, 'John Doe',  '1985-06-15', 'Male',   '+1-555-0201', 'O+',
   JSON_OBJECT('allergies', JSON_ARRAY('Penicillin'), 'chronic_conditions', JSON_ARRAY('Hypertension'))),
  (5, 'Mary Jane', '1992-03-22', 'Female', '+1-555-0202', 'A+',
   JSON_OBJECT('allergies', JSON_ARRAY(), 'chronic_conditions', JSON_ARRAY('Asthma')));

-- ── Inventory ──────────────────────────────────────────────
INSERT INTO Inventory (drug_name, generic_name, unit, unit_price, stock_qty, reorder_level) VALUES
  ('Paracetamol 500mg', 'Acetaminophen', 'tablet',  0.10, 500, 50),
  ('Amoxicillin 250mg', 'Amoxicillin',   'capsule', 0.35, 200, 30),
  ('Metformin 500mg',   'Metformin',     'tablet',  0.20, 300, 40),
  ('Atorvastatin 20mg', 'Atorvastatin',  'tablet',  0.45, 150, 25),
  ('Salbutamol Inhaler','Albuterol',     'inhaler', 8.50,  40, 10),
  ('Amlodipine 5mg',    'Amlodipine',    'tablet',  0.30, 250, 30);
