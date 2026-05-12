-- ============================================
-- HOSPITAL MANAGEMENT SYSTEM V2
-- With Login, Roles, Diagnosis, Lab Reports
-- Normalized to 3NF
-- ============================================

CREATE DATABASE IF NOT EXISTS hospital_v2;
USE hospital_v2;

-- Department table
CREATE TABLE Department (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    dept_description VARCHAR(255)
);

-- Users table (Admin, Doctor, Receptionist, Patient)
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'doctor', 'receptionist', 'patient') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Doctor table
CREATE TABLE Doctor (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    available_days VARCHAR(100) DEFAULT 'Mon-Sat',
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
);

-- Patient table
CREATE TABLE Patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    age INT,
    gender ENUM('Male', 'Female', 'Other'),
    address VARCHAR(255),
    blood_group VARCHAR(5),
    registered_on DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Appointment table
CREATE TABLE Appointment (
    appt_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appt_date DATE NOT NULL,
    appt_time TIME NOT NULL,
    status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id) ON DELETE CASCADE
);

-- Diagnosis Report table
CREATE TABLE DiagnosisReport (
    diag_id INT AUTO_INCREMENT PRIMARY KEY,
    appt_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    diagnosis TEXT NOT NULL,
    prescription TEXT,
    follow_up_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appt_id) REFERENCES Appointment(appt_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id) ON DELETE CASCADE
);

-- Lab Report table
CREATE TABLE LabReport (
    lab_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    test_name VARCHAR(150) NOT NULL,
    result TEXT NOT NULL,
    normal_range VARCHAR(100),
    status ENUM('Normal', 'Abnormal', 'Critical') DEFAULT 'Normal',
    test_date DATE NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id) ON DELETE CASCADE
);

-- Billing table
CREATE TABLE Billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    appt_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('Pending', 'Paid', 'Cancelled') DEFAULT 'Pending',
    payment_date DATE,
    description VARCHAR(255),
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (appt_id) REFERENCES Appointment(appt_id) ON DELETE CASCADE
);

-- ============================================
-- SAMPLE DATA
-- ============================================

INSERT INTO Department (dept_name, dept_description) VALUES
('Cardiology', 'Heart and cardiovascular care'),
('Neurology', 'Brain and nervous system'),
('Orthopedics', 'Bones, joints and muscles'),
('General Medicine', 'General health and wellness'),
('Pediatrics', 'Child healthcare'),
('Dermatology', 'Skin care'),
('ENT', 'Ear, Nose and Throat'),
('Ophthalmology', 'Eye care'),
('Psychiatry', 'Mental health'),
('Gynecology', 'Women health');

-- Admin user (password: admin123)
INSERT INTO Users (name, phone, email, password, role) VALUES
('Admin', '9000000000', 'admin@hospital.com', 'admin123', 'admin');

-- Receptionist (password: recept123)
INSERT INTO Users (name, phone, email, password, role) VALUES
('Receptionist', '9000000001', 'recept@hospital.com', 'recept123', 'receptionist');

-- 10 Doctors (password: doctor123)
INSERT INTO Users (name, phone, email, password, role) VALUES
('Dr. Arjun Mehta', '9876501001', 'arjun@hospital.com', 'doctor123', 'doctor'),
('Dr. Priya Sharma', '9876501002', 'priya@hospital.com', 'doctor123', 'doctor'),
('Dr. Ravi Kumar', '9876501003', 'ravi@hospital.com', 'doctor123', 'doctor'),
('Dr. Sunita Rao', '9876501004', 'sunita@hospital.com', 'doctor123', 'doctor'),
('Dr. Anil Nair', '9876501005', 'anil@hospital.com', 'doctor123', 'doctor'),
('Dr. Kavya Reddy', '9876501006', 'kavya@hospital.com', 'doctor123', 'doctor'),
('Dr. Suresh Babu', '9876501007', 'suresh@hospital.com', 'doctor123', 'doctor'),
('Dr. Meena Iyer', '9876501008', 'meena@hospital.com', 'doctor123', 'doctor'),
('Dr. Rajesh Pillai', '9876501009', 'rajesh@hospital.com', 'doctor123', 'doctor'),
('Dr. Deepa Nair', '9876501010', 'deepa@hospital.com', 'doctor123', 'doctor');

-- Doctor profiles (user_id 3-12)
INSERT INTO Doctor (user_id, specialization, dept_id) VALUES
(3, 'Cardiologist', 1),
(4, 'Neurologist', 2),
(5, 'Orthopedic Surgeon', 3),
(6, 'General Physician', 4),
(7, 'Pediatrician', 5),
(8, 'Dermatologist', 6),
(9, 'ENT Specialist', 7),
(10, 'Ophthalmologist', 8),
(11, 'Psychiatrist', 9),
(12, 'Gynecologist', 10);
