import mysql.connector

# UPDATE THESE with your Railway credentials
db = mysql.connector.connect(
    host="viaduct.proxy.rlwy.net",
    port=30514,
    user="root",
    password="ZzETMKDuAMkbXFdjhtRAVDSkTVtpkAIV",
    database="mysql"
)
cursor = db.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS railway")
cursor.execute("USE railway")

cursor = db.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS Department (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    dept_description VARCHAR(255)
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','doctor','receptionist','patient') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Doctor (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    available_days VARCHAR(100) DEFAULT 'Mon-Sat',
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    age INT,
    gender ENUM('Male','Female','Other'),
    address VARCHAR(255),
    blood_group VARCHAR(5),
    registered_on DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Appointment (
    appt_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appt_date DATE NOT NULL,
    appt_time TIME NOT NULL,
    status ENUM('Scheduled','Completed','Cancelled') DEFAULT 'Scheduled',
    notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id) ON DELETE CASCADE
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS DiagnosisReport (
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
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS LabReport (
    lab_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    test_name VARCHAR(150) NOT NULL,
    result TEXT NOT NULL,
    normal_range VARCHAR(100),
    status ENUM('Normal','Abnormal','Critical') DEFAULT 'Normal',
    test_date DATE NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id) ON DELETE CASCADE
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    appt_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('Pending','Paid','Cancelled') DEFAULT 'Pending',
    payment_date DATE,
    description VARCHAR(255),
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (appt_id) REFERENCES Appointment(appt_id) ON DELETE CASCADE
)""")

# Sample data
cursor.execute("INSERT IGNORE INTO Department (dept_name,dept_description) VALUES ('Cardiology','Heart care'),('Neurology','Brain care'),('Orthopedics','Bone care'),('General Medicine','General health'),('Pediatrics','Child health'),('Dermatology','Skin care'),('ENT','Ear Nose Throat'),('Ophthalmology','Eye care'),('Psychiatry','Mental health'),('Gynecology','Women health')")

cursor.execute("INSERT IGNORE INTO Users (name,phone,email,password,role) VALUES ('Admin','9000000000','admin@hospital.com','admin123','admin'),('Receptionist','9000000001','recept@hospital.com','recept123','receptionist'),('Dr. Arjun Mehta','9876501001','arjun@hospital.com','doctor123','doctor'),('Dr. Priya Sharma','9876501002','priya@hospital.com','doctor123','doctor'),('Dr. Ravi Kumar','9876501003','ravi@hospital.com','doctor123','doctor'),('Dr. Sunita Rao','9876501004','sunita@hospital.com','doctor123','doctor'),('Dr. Anil Nair','9876501005','anil@hospital.com','doctor123','doctor'),('Dr. Kavya Reddy','9876501006','kavya@hospital.com','doctor123','doctor'),('Dr. Suresh Babu','9876501007','suresh@hospital.com','doctor123','doctor'),('Dr. Meena Iyer','9876501008','meena@hospital.com','doctor123','doctor'),('Dr. Rajesh Pillai','9876501009','rajesh@hospital.com','doctor123','doctor'),('Dr. Deepa Nair','9876501010','deepa@hospital.com','doctor123','doctor')")

# Get doctor user IDs dynamically
doctors = [
    ('9876501001', 'Cardiologist', 1),
    ('9876501002', 'Neurologist', 2),
    ('9876501003', 'Orthopedic Surgeon', 3),
    ('9876501004', 'General Physician', 4),
    ('9876501005', 'Pediatrician', 5),
    ('9876501006', 'Dermatologist', 6),
    ('9876501007', 'ENT Specialist', 7),
    ('9876501008', 'Ophthalmologist', 8),
    ('9876501009', 'Psychiatrist', 9),
    ('9876501010', 'Gynecologist', 10),
]

for phone, specialization, dept_id in doctors:
    cursor.execute("SELECT user_id FROM Users WHERE phone=%s", (phone,))
    row = cursor.fetchone()
    if row:
        uid = row[0]
        cursor.execute("INSERT IGNORE INTO Doctor (user_id,specialization,dept_id) VALUES (%s,%s,%s)", (uid, specialization, dept_id))

db.commit()
print("✅ All tables created and sample data inserted!")
print("✅ Admin login: 9000000000 / admin123")
print("✅ Doctor login: 9876501001 / doctor123")
print("✅ Receptionist: 9000000001 / recept123")
cursor.close()
db.close()
