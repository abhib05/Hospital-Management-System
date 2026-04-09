-- ============================================================
-- HMS Extended Seed Data  (related rows across all 10 tables)
-- Passwords are bcrypt hashes of "Password123!"
-- Safe to re-run: cleans up previous extended data first
-- ============================================================
USE hms_db;

-- ── Cleanup (delete in reverse FK order to avoid constraint errors) ──────────
DELETE FROM Audit_Logs     WHERE id BETWEEN 1 AND 20;
DELETE FROM Lab_Tests      WHERE id BETWEEN 1 AND 9;
DELETE FROM Dispensed_Items WHERE id BETWEEN 1 AND 10;
DELETE FROM Invoices       WHERE id BETWEEN 1 AND 5;
DELETE FROM Medical_Records WHERE id BETWEEN 1 AND 5;
DELETE FROM Appointments   WHERE id BETWEEN 1 AND 8;
DELETE FROM Patients       WHERE id BETWEEN 3 AND 5;
DELETE FROM Doctors        WHERE id = 3;
DELETE FROM Users          WHERE id BETWEEN 8 AND 11;
DELETE FROM Inventory      WHERE id BETWEEN 7 AND 10;

-- ──────────────────────────────────────────────
-- 1. USERS  (3 new: 1 Doctor, 2 Patients, 1 Pharmacist)
--    Existing IDs: 1-7  →  New IDs: 8-11
-- ──────────────────────────────────────────────
INSERT INTO Users (id, username, password_hash, role) VALUES
  (8,  'dr_patel',      '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Doctor'),
  (9,  'patient_alice', '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Patient'),
  (10, 'patient_bob',   '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Patient'),
  (11, 'patient_carol', '$2b$12$eIG8Mk6O2fdLgDs3G6wDY.UUHjoJbDnNlCw6AaomPo.vv84hAcWzO', 'Patient');

-- ──────────────────────────────────────────────
-- 2. DOCTORS  (1 new)
--    Existing IDs: 1 (dr_smith/user 2), 2 (dr_chen/user 3)
--    New ID: 3 → user_id=8 (dr_patel)
-- ──────────────────────────────────────────────
INSERT INTO Doctors (id, user_id, full_name, specialization, fees, phone) VALUES
  (3, 8, 'Dr. Priya Patel', 'Neurology', 200.00, '+1-555-0103');

-- ──────────────────────────────────────────────
-- 3. PATIENTS  (3 new)
--    Existing IDs: 1 (John Doe/user 4), 2 (Mary Jane/user 5)
--    New IDs: 3, 4, 5 → user_ids 9, 10, 11
-- ──────────────────────────────────────────────
INSERT INTO Patients (id, user_id, full_name, dob, gender, phone, blood_group, medical_history) VALUES
  (3, 9,  'Alice Brown', '1990-08-14', 'Female', '+1-555-0301', 'B+',
   JSON_OBJECT('allergies', JSON_ARRAY('Sulfa'), 'chronic_conditions', JSON_ARRAY('Asthma'))),
  (4, 10, 'Bob Wilson',  '1978-11-03', 'Male',   '+1-555-0302', 'AB+',
   JSON_OBJECT('allergies', JSON_ARRAY(), 'chronic_conditions', JSON_ARRAY('Diabetes', 'Hypertension'))),
  (5, 11, 'Carol Davis', '2001-04-27', 'Female', '+1-555-0303', 'O-',
   JSON_OBJECT('allergies', JSON_ARRAY('Aspirin'), 'chronic_conditions', JSON_ARRAY()));

-- ──────────────────────────────────────────────
-- 4. INVENTORY  (4 new drugs)
--    Existing IDs: 1-6  →  New IDs: 7-10
-- ──────────────────────────────────────────────
INSERT INTO Inventory (id, drug_name, generic_name, unit, unit_price, stock_qty, reorder_level) VALUES
  (7,  'Lisinopril 10mg',   'Lisinopril',    'tablet',  0.25, 180, 30),
  (8,  'Ibuprofen 400mg',   'Ibuprofen',     'tablet',  0.15, 400, 60),
  (9,  'Omeprazole 20mg',   'Omeprazole',    'capsule', 0.40, 220, 35),
  (10, 'Cetirizine 10mg',   'Cetirizine',    'tablet',  0.12, 300, 40);

-- ──────────────────────────────────────────────
-- 5. APPOINTMENTS  (8 rows)
--    patient_id refs Patients.id   (1–5)
--    doctor_id  refs Doctors.id    (1–3)
-- ──────────────────────────────────────────────
INSERT INTO Appointments (id, patient_id, doctor_id, scheduled_at, status, reason) VALUES
  (1, 1, 1, '2026-03-10 09:00:00', 'Completed', 'Routine check-up and blood pressure review'),
  (2, 2, 2, '2026-03-11 10:30:00', 'Completed', 'Chest pain and palpitations'),
  (3, 3, 1, '2026-03-12 11:00:00', 'Completed', 'Asthma flare-up, breathing difficulties'),
  (4, 4, 3, '2026-03-15 14:00:00', 'Completed', 'Persistent headaches and dizziness'),
  (5, 5, 1, '2026-03-18 15:00:00', 'Completed', 'Stomach pain and nausea'),
  (6, 1, 2, '2026-04-10 09:30:00', 'Scheduled', 'Follow-up cardiac screening'),
  (7, 2, 3, '2026-04-11 11:00:00', 'Scheduled', 'Migraine assessment'),
  (8, 4, 1, '2026-03-20 13:00:00', 'No-Show',   'Diabetes management review');

-- ──────────────────────────────────────────────
-- 6. MEDICAL RECORDS  (5 rows — one per Completed appointment)
--    appointment_id refs Appointments.id  (1–5 are Completed)
--    patient_id     refs Patients.id
--    doctor_id      refs Doctors.id
-- ──────────────────────────────────────────────
INSERT INTO Medical_Records (id, appointment_id, patient_id, doctor_id, diagnosis, notes, prescriptions, lab_results) VALUES
  (1, 1, 1, 1,
   'Stage 1 Hypertension',
   'Patient presents with BP 148/92. Advised low-sodium diet and increased physical activity. Medication adjusted.',
   JSON_ARRAY(
     JSON_OBJECT('drug', 'Metformin 500mg',   'dose', '500mg', 'frequency', 'twice daily', 'duration', '30 days'),
     JSON_OBJECT('drug', 'Paracetamol 500mg', 'dose', '500mg', 'frequency', 'as needed',   'duration', '10 days')
   ),
   JSON_OBJECT('blood_pressure', '148/92', 'pulse', '78 bpm')),

  (2, 2, 2, 2,
   'Paroxysmal Atrial Fibrillation',
   'ECG confirms intermittent AF. Starting rate control therapy. Referred for echocardiogram.',
   JSON_ARRAY(
     JSON_OBJECT('drug', 'Atorvastatin 20mg', 'dose', '20mg', 'frequency', 'once daily at night', 'duration', '30 days'),
     JSON_OBJECT('drug', 'Amlodipine 5mg',    'dose', '5mg',  'frequency', 'once daily',          'duration', '30 days')
   ),
   JSON_OBJECT('ecg', 'Irregular rhythm - AF pattern', 'heart_rate', '96 bpm')),

  (3, 3, 3, 1,
   'Moderate Persistent Asthma',
   'Spirometry shows FEV1 at 68%. Inhaler technique corrected. Step-up therapy initiated.',
   JSON_ARRAY(
     JSON_OBJECT('drug', 'Salbutamol Inhaler', 'dose', '2 puffs', 'frequency', 'as needed', 'duration', '60 days'),
     JSON_OBJECT('drug', 'Cetirizine 10mg',    'dose', '10mg',    'frequency', 'once daily', 'duration', '14 days')
   ),
   JSON_OBJECT('spirometry', 'FEV1 68% predicted', 'peak_flow', '320 L/min')),

  (4, 4, 4, 3,
   'Tension-Type Headache with Cervical Spondylosis',
   'MRI ordered. Neurological exam normal. Likely cervicogenic origin. Physiotherapy recommended.',
   JSON_ARRAY(
     JSON_OBJECT('drug', 'Ibuprofen 400mg',  'dose', '400mg', 'frequency', 'three times daily with food', 'duration', '7 days'),
     JSON_OBJECT('drug', 'Lisinopril 10mg',  'dose', '10mg',  'frequency', 'once daily',                  'duration', '30 days')
   ),
   JSON_OBJECT('neurological_exam', 'Normal reflexes', 'cervical_range', 'Reduced flexion')),

  (5, 5, 5, 1,
   'Acute Gastritis',
   'Epigastric tenderness on palpation. H. pylori test ordered. Avoid NSAIDs and spicy food.',
   JSON_ARRAY(
     JSON_OBJECT('drug', 'Omeprazole 20mg',  'dose', '20mg', 'frequency', 'twice daily before meals', 'duration', '14 days'),
     JSON_OBJECT('drug', 'Paracetamol 500mg','dose', '500mg','frequency', 'as needed',                 'duration', '5 days')
   ),
   JSON_OBJECT('h_pylori_test', 'Pending', 'ultrasound', 'Mild gastric wall thickening'));

-- ──────────────────────────────────────────────
-- 7. DISPENSED_ITEMS
--    record_id    refs Medical_Records.id  (1–5)
--    inventory_id refs Inventory.id        (1–10)
--    dispensed_by refs Users.id            (6 = pharmacist1)
-- ──────────────────────────────────────────────
INSERT INTO Dispensed_Items (id, record_id, inventory_id, quantity, dispensed_by) VALUES
  -- Record 1: Hypertension (Metformin + Paracetamol)
  (1, 1, 3, 60, 6),   -- Metformin 500mg × 60 tablets
  (2, 1, 1, 10, 6),   -- Paracetamol 500mg × 10 tablets
  -- Record 2: AF (Atorvastatin + Amlodipine)
  (3, 2, 4, 30, 6),   -- Atorvastatin 20mg × 30 tablets
  (4, 2, 6, 30, 6),   -- Amlodipine 5mg × 30 tablets
  -- Record 3: Asthma (Salbutamol + Cetirizine)
  (5, 3, 5,  2, 6),   -- Salbutamol Inhaler × 2
  (6, 3, 10, 14, 6),  -- Cetirizine 10mg × 14 tablets
  -- Record 4: Headache (Ibuprofen + Lisinopril)
  (7, 4, 8, 21, 6),   -- Ibuprofen 400mg × 21 tablets
  (8, 4, 7, 30, 6),   -- Lisinopril 10mg × 30 tablets
  -- Record 5: Gastritis (Omeprazole + Paracetamol)
  (9,  5, 9, 28, 6),  -- Omeprazole 20mg × 28 capsules
  (10, 5, 1, 10, 6);  -- Paracetamol 500mg × 10 tablets

-- ──────────────────────────────────────────────
-- 8. INVOICES  (one per Completed appointment)
--    patient_id     refs Patients.id
--    appointment_id refs Appointments.id  (1–5)
--    pharmacy_total calculated from dispensed items above
-- ──────────────────────────────────────────────
INSERT INTO Invoices (id, patient_id, appointment_id, consultation_fee, pharmacy_total, payment_status) VALUES
  -- Appt 1: John Doe, Dr. Smith. Metformin 60×0.20=12 + Paracetamol 10×0.10=1 → 13.00
  (1, 1, 1, 150.00, 13.00, 'Paid'),
  -- Appt 2: Mary Jane, Dr. Chen. Atorvastatin 30×0.45=13.50 + Amlodipine 30×0.30=9.00 → 22.50
  (2, 2, 2, 250.00, 22.50, 'Paid'),
  -- Appt 3: Alice Brown, Dr. Smith. Salbutamol 2×8.50=17 + Cetirizine 14×0.12=1.68 → 18.68
  (3, 3, 3, 150.00, 18.68, 'Paid'),
  -- Appt 4: Bob Wilson, Dr. Patel. Ibuprofen 21×0.15=3.15 + Lisinopril 30×0.25=7.50 → 10.65
  (4, 4, 4, 200.00, 10.65, 'Pending'),
  -- Appt 5: Carol Davis, Dr. Smith. Omeprazole 28×0.40=11.20 + Paracetamol 10×0.10=1.00 → 12.20
  (5, 5, 5, 150.00, 12.20, 'Pending');

-- ──────────────────────────────────────────────
-- 9. LAB_TESTS
--    record_id  refs Medical_Records.id  (1–5)
--    ordered_by refs Doctors.id          (1–3)
--    assigned_to refs Users.id           (7 = labtech1)
-- ──────────────────────────────────────────────
INSERT INTO Lab_Tests (id, record_id, test_name, ordered_by, assigned_to, status, result_notes) VALUES
  (1, 1, 'Complete Blood Count (CBC)',         1, 7, 'Completed',   'WBC 7.2, RBC 4.8, Hgb 13.5 — within normal range'),
  (2, 1, 'Lipid Panel',                        1, 7, 'Completed',   'LDL 142 mg/dL (elevated), HDL 38 mg/dL (low) — dietary changes advised'),
  (3, 2, 'Electrocardiogram (ECG)',             2, 7, 'Completed',   'Irregular rhythm confirmed. AF pattern. Referred to cardiologist.'),
  (4, 2, 'Echocardiogram',                     2, 7, 'In-Progress', 'Scheduled for next week. Patient notified.'),
  (5, 3, 'Spirometry / Pulmonary Function',    1, 7, 'Completed',   'FEV1/FVC ratio 0.68 — moderate obstruction pattern'),
  (6, 4, 'MRI Brain with Contrast',            3, 7, 'In-Progress', 'Scan performed. Radiologist report pending.'),
  (7, 4, 'Cervical Spine X-Ray',               3, 7, 'Completed',   'C4-C5 disc space narrowing noted. Osteophyte formation.'),
  (8, 5, 'H. Pylori Breath Test',              1, 7, 'Ordered',     NULL),
  (9, 5, 'Abdominal Ultrasound',               1, 7, 'Completed',   'Mild gastric wall thickening. No masses or gallstones detected.');

-- ──────────────────────────────────────────────
-- 10. AUDIT_LOGS
--     user_id refs Users.id  (NULL for system actions)
-- ──────────────────────────────────────────────
INSERT INTO Audit_Logs (id, user_id, action, target_table, target_id, details, ip_address) VALUES
  (1,  2,    'LOGIN',   'Users',           2,    '{"username":"dr_smith"}',                          '192.168.1.10'),
  (2,  3,    'LOGIN',   'Users',           3,    '{"username":"dr_chen"}',                           '192.168.1.11'),
  (3,  4,    'LOGIN',   'Users',           4,    '{"username":"patient_john"}',                      '192.168.1.20'),
  (4,  5,    'LOGIN',   'Users',           5,    '{"username":"patient_mary"}',                      '192.168.1.21'),
  (5,  6,    'LOGIN',   'Users',           6,    '{"username":"pharmacist1"}',                       '192.168.1.30'),
  (6,  2,    'CREATE',  'Appointments',    1,    '{"patient_id":1,"doctor_id":1,"status":"Scheduled"}', '192.168.1.10'),
  (7,  3,    'CREATE',  'Appointments',    2,    '{"patient_id":2,"doctor_id":2,"status":"Scheduled"}', '192.168.1.11'),
  (8,  2,    'UPDATE',  'Appointments',    1,    '{"status":"Completed"}',                           '192.168.1.10'),
  (9,  3,    'UPDATE',  'Appointments',    2,    '{"status":"Completed"}',                           '192.168.1.11'),
  (10, 2,    'CREATE',  'Medical_Records', 1,    '{"appointment_id":1,"diagnosis":"Stage 1 Hypertension"}', '192.168.1.10'),
  (11, 3,    'CREATE',  'Medical_Records', 2,    '{"appointment_id":2,"diagnosis":"Paroxysmal AF"}', '192.168.1.11'),
  (12, 6,    'DISPENSE','Dispensed_Items', 1,    '{"drug":"Metformin 500mg","qty":60,"record_id":1}', '192.168.1.30'),
  (13, 6,    'DISPENSE','Dispensed_Items', 3,    '{"drug":"Atorvastatin 20mg","qty":30,"record_id":2}','192.168.1.30'),
  (14, 4,    'VIEW',    'Medical_Records', 1,    '{"note":"Patient viewed own record — masked"}',    '192.168.1.20'),
  (15, 4,    'VIEW',    'Patients',        1,    '{"endpoint":"/api/patients/me/full","unmasked":true}','192.168.1.20'),
  (16, 1,    'CREATE',  'Inventory',       7,    '{"drug":"Lisinopril 10mg","stock":180}',           '192.168.1.1'),
  (17, 1,    'CREATE',  'Users',           8,    '{"username":"dr_patel","role":"Doctor"}',           '192.168.1.1'),
  (18, 7,    'UPDATE',  'Lab_Tests',       1,    '{"status":"Completed","result":"CBC normal range"}','192.168.1.40'),
  (19, 7,    'UPDATE',  'Lab_Tests',       3,    '{"status":"Completed","result":"AF confirmed"}',   '192.168.1.40'),
  (20, NULL, 'VIEW',    'Audit_Logs',      NULL, '{"note":"System health check"}',                   NULL);
