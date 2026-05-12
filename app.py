from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'hospital_v2_secret_key'

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# ============================================
# DATABASE CONNECTION
# ============================================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="hospital_v2"
    )

# ============================================
# LOGIN REQUIRED DECORATORS
# ============================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ============================================
# AUTH ROUTES
# ============================================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE phone = %s AND password = %s", (phone, password))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if user:
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['phone'] = user['phone']
            if user['role'] == 'patient':
                db2 = get_db()
                cur2 = db2.cursor(dictionary=True)
                cur2.execute("SELECT patient_id FROM Patient WHERE user_id = %s", (user['user_id'],))
                p = cur2.fetchone()
                cur2.close()
                db2.close()
                if p:
                    session['patient_id'] = p['patient_id']
            elif user['role'] == 'doctor':
                db2 = get_db()
                cur2 = db2.cursor(dictionary=True)
                cur2.execute("SELECT doctor_id FROM Doctor WHERE user_id = %s", (user['user_id'],))
                d = cur2.fetchone()
                cur2.close()
                db2.close()
                if d:
                    session['doctor_id'] = d['doctor_id']
            flash(f'Welcome, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid phone or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO Users (name, phone, email, password, role)
                VALUES (%s, %s, %s, %s, 'patient')
            """, (request.form['name'], request.form['phone'],
                  request.form['email'], request.form['password']))
            user_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO Patient (user_id, age, gender, address, blood_group)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, request.form['age'], request.form['gender'],
                  request.form['address'], request.form['blood_group']))
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Phone number or email already exists!', 'danger')
        finally:
            cursor.close()
            db.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ============================================
# DASHBOARD (role based)
# ============================================
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    role = session['role']

    if role == 'patient':
        pid = session.get('patient_id')
        cursor.execute("SELECT COUNT(*) as c FROM Appointment WHERE patient_id=%s", (pid,))
        total_appts = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM DiagnosisReport WHERE patient_id=%s", (pid,))
        total_diag = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM LabReport WHERE patient_id=%s", (pid,))
        total_lab = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM Billing WHERE patient_id=%s AND payment_status='Pending'", (pid,))
        pending_bills = cursor.fetchone()['c']
        cursor.execute("""
            SELECT a.appt_id, u.name as doctor_name, a.appt_date, a.appt_time, a.status
            FROM Appointment a JOIN Doctor d ON a.doctor_id=d.doctor_id
            JOIN Users u ON d.user_id=u.user_id
            WHERE a.patient_id=%s ORDER BY a.appt_date DESC LIMIT 5
        """, (pid,))
        recent_appts = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('patient_dashboard.html',
            total_appts=total_appts, total_diag=total_diag,
            total_lab=total_lab, pending_bills=pending_bills,
            recent_appts=recent_appts)

    elif role == 'doctor':
        did = session.get('doctor_id')
        cursor.execute("SELECT COUNT(*) as c FROM Appointment WHERE doctor_id=%s AND appt_date=CURDATE()", (did,))
        todays = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM Appointment WHERE doctor_id=%s AND status='Scheduled'", (did,))
        scheduled = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM DiagnosisReport WHERE doctor_id=%s", (did,))
        total_diag = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM LabReport WHERE doctor_id=%s", (did,))
        total_lab = cursor.fetchone()['c']
        cursor.execute("""
            SELECT a.appt_id, u.name as patient_name, a.appt_date, a.appt_time, a.status
            FROM Appointment a JOIN Patient p ON a.patient_id=p.patient_id
            JOIN Users u ON p.user_id=u.user_id
            WHERE a.doctor_id=%s ORDER BY a.appt_date DESC LIMIT 5
        """, (did,))
        recent_appts = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('doctor_dashboard.html',
            todays=todays, scheduled=scheduled,
            total_diag=total_diag, total_lab=total_lab,
            recent_appts=recent_appts)

    else:
        cursor.execute("SELECT COUNT(*) as c FROM Patient")
        total_patients = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM Doctor")
        total_doctors = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM Appointment WHERE appt_date=CURDATE()")
        todays_appts = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM Billing WHERE payment_status='Pending'")
        pending_bills = cursor.fetchone()['c']
        cursor.execute("""
            SELECT a.appt_id, pu.name as patient_name, du.name as doctor_name,
                   a.appt_date, a.appt_time, a.status
            FROM Appointment a
            JOIN Patient p ON a.patient_id=p.patient_id
            JOIN Users pu ON p.user_id=pu.user_id
            JOIN Doctor d ON a.doctor_id=d.doctor_id
            JOIN Users du ON d.user_id=du.user_id
            ORDER BY a.appt_date DESC LIMIT 5
        """)
        recent_appts = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('dashboard.html',
            total_patients=total_patients, total_doctors=total_doctors,
            todays_appts=todays_appts, pending_bills=pending_bills,
            recent_appts=recent_appts)

# ============================================
# PATIENTS
# ============================================
@app.route('/patients')
@login_required
@role_required('admin', 'receptionist')
def patients():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, u.name, u.phone, u.email FROM Patient p
        JOIN Users u ON p.user_id=u.user_id ORDER BY p.registered_on DESC
    """)
    patients = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('patients.html', patients=patients)

@app.route('/patients/delete/<int:patient_id>')
@login_required
@role_required('admin')
def delete_patient(patient_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM Patient WHERE patient_id=%s", (patient_id,))
    p = cursor.fetchone()
    if p:
        cursor.execute("DELETE FROM Users WHERE user_id=%s", (p[0],))
        db.commit()
    cursor.close()
    db.close()
    flash('Patient deleted.', 'info')
    return redirect(url_for('patients'))

# ============================================
# DOCTORS
# ============================================
@app.route('/doctors')
@login_required
def doctors():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.*, u.name, u.phone, u.email, dept.dept_name
        FROM Doctor d JOIN Users u ON d.user_id=u.user_id
        JOIN Department dept ON d.dept_id=dept.dept_id
    """)
    doctors = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('doctors.html', doctors=doctors)

# ============================================
# APPOINTMENTS
# ============================================
@app.route('/appointments')
@login_required
def appointments():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    role = session['role']

    if role == 'patient':
        pid = session.get('patient_id')
        cursor.execute("""
            SELECT a.*, du.name as doctor_name, d.specialization
            FROM Appointment a JOIN Doctor d ON a.doctor_id=d.doctor_id
            JOIN Users du ON d.user_id=du.user_id
            WHERE a.patient_id=%s ORDER BY a.appt_date DESC
        """, (pid,))
    elif role == 'doctor':
        did = session.get('doctor_id')
        cursor.execute("""
            SELECT a.*, pu.name as patient_name
            FROM Appointment a JOIN Patient p ON a.patient_id=p.patient_id
            JOIN Users pu ON p.user_id=pu.user_id
            WHERE a.doctor_id=%s ORDER BY a.appt_date DESC
        """, (did,))
    else:
        cursor.execute("""
            SELECT a.*, pu.name as patient_name, du.name as doctor_name, d.specialization
            FROM Appointment a
            JOIN Patient p ON a.patient_id=p.patient_id JOIN Users pu ON p.user_id=pu.user_id
            JOIN Doctor d ON a.doctor_id=d.doctor_id JOIN Users du ON d.user_id=du.user_id
            ORDER BY a.appt_date DESC
        """)
    appointments = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('appointments.html', appointments=appointments)

@app.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            cursor.execute("""
                INSERT INTO Appointment (patient_id, doctor_id, appt_date, appt_time, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (request.form['patient_id'], request.form['doctor_id'],
                  request.form['appt_date'], request.form['appt_time'], request.form['notes']))
            db.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('appointments'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    cursor.execute("""
        SELECT p.patient_id, u.name, u.phone FROM Patient p
        JOIN Users u ON p.user_id=u.user_id ORDER BY u.name
    """)
    patients = cursor.fetchall()
    cursor.execute("""
        SELECT d.doctor_id, u.name, d.specialization, dept.dept_name
        FROM Doctor d JOIN Users u ON d.user_id=u.user_id
        JOIN Department dept ON d.dept_id=dept.dept_id
    """)
    doctors = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('book_appointment.html', patients=patients, doctors=doctors)

@app.route('/appointments/update/<int:appt_id>/<status>')
@login_required
def update_appointment(appt_id, status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE Appointment SET status=%s WHERE appt_id=%s", (status, appt_id))
    db.commit()
    cursor.close()
    db.close()
    flash(f'Appointment marked as {status}.', 'info')
    return redirect(url_for('appointments'))

# ============================================
# DIAGNOSIS REPORTS
# ============================================
@app.route('/diagnosis')
@login_required
def diagnosis():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    role = session['role']
    if role == 'patient':
        pid = session.get('patient_id')
        cursor.execute("""
            SELECT dr.*, du.name as doctor_name, a.appt_date
            FROM DiagnosisReport dr JOIN Doctor d ON dr.doctor_id=d.doctor_id
            JOIN Users du ON d.user_id=du.user_id
            JOIN Appointment a ON dr.appt_id=a.appt_id
            WHERE dr.patient_id=%s ORDER BY dr.created_at DESC
        """, (pid,))
    elif role == 'doctor':
        did = session.get('doctor_id')
        cursor.execute("""
            SELECT dr.*, pu.name as patient_name, a.appt_date
            FROM DiagnosisReport dr JOIN Patient p ON dr.patient_id=p.patient_id
            JOIN Users pu ON p.user_id=pu.user_id
            JOIN Appointment a ON dr.appt_id=a.appt_id
            WHERE dr.doctor_id=%s ORDER BY dr.created_at DESC
        """, (did,))
    else:
        cursor.execute("""
            SELECT dr.*, pu.name as patient_name, du.name as doctor_name, a.appt_date
            FROM DiagnosisReport dr
            JOIN Patient p ON dr.patient_id=p.patient_id JOIN Users pu ON p.user_id=pu.user_id
            JOIN Doctor d ON dr.doctor_id=d.doctor_id JOIN Users du ON d.user_id=du.user_id
            JOIN Appointment a ON dr.appt_id=a.appt_id
            ORDER BY dr.created_at DESC
        """)
    reports = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('diagnosis.html', reports=reports)

@app.route('/diagnosis/add', methods=['GET', 'POST'])
@login_required
@role_required('doctor', 'admin')
def add_diagnosis():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            cursor.execute("""
                INSERT INTO DiagnosisReport (appt_id, patient_id, doctor_id, diagnosis, prescription, follow_up_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (request.form['appt_id'], request.form['patient_id'],
                  request.form['doctor_id'], request.form['diagnosis'],
                  request.form['prescription'],
                  request.form['follow_up_date'] or None))
            cursor.execute("UPDATE Appointment SET status='Completed' WHERE appt_id=%s", (request.form['appt_id'],))
            db.commit()
            flash('Diagnosis report added!', 'success')
            return redirect(url_for('diagnosis'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    did = session.get('doctor_id')
    if session['role'] == 'doctor':
        cursor.execute("""
            SELECT a.appt_id, pu.name as patient_name, p.patient_id, a.appt_date
            FROM Appointment a JOIN Patient p ON a.patient_id=p.patient_id
            JOIN Users pu ON p.user_id=pu.user_id
            WHERE a.doctor_id=%s AND a.status='Scheduled'
        """, (did,))
        appointments = cursor.fetchall()
        doctor_id = did
    else:
        cursor.execute("""
            SELECT a.appt_id, pu.name as patient_name, p.patient_id, a.appt_date, d.doctor_id
            FROM Appointment a JOIN Patient p ON a.patient_id=p.patient_id
            JOIN Users pu ON p.user_id=pu.user_id
            JOIN Doctor d ON a.doctor_id=d.doctor_id
            WHERE a.status='Scheduled'
        """)
        appointments = cursor.fetchall()
        doctor_id = None
    cursor.close()
    db.close()
    return render_template('add_diagnosis.html', appointments=appointments, doctor_id=doctor_id)

# ============================================
# LAB REPORTS
# ============================================
@app.route('/lab')
@login_required
def lab_reports():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    role = session['role']
    if role == 'patient':
        pid = session.get('patient_id')
        cursor.execute("""
            SELECT lr.*, du.name as doctor_name FROM LabReport lr
            JOIN Doctor d ON lr.doctor_id=d.doctor_id JOIN Users du ON d.user_id=du.user_id
            WHERE lr.patient_id=%s ORDER BY lr.test_date DESC
        """, (pid,))
    elif role == 'doctor':
        did = session.get('doctor_id')
        cursor.execute("""
            SELECT lr.*, pu.name as patient_name FROM LabReport lr
            JOIN Patient p ON lr.patient_id=p.patient_id JOIN Users pu ON p.user_id=pu.user_id
            WHERE lr.doctor_id=%s ORDER BY lr.test_date DESC
        """, (did,))
    else:
        cursor.execute("""
            SELECT lr.*, pu.name as patient_name, du.name as doctor_name
            FROM LabReport lr
            JOIN Patient p ON lr.patient_id=p.patient_id JOIN Users pu ON p.user_id=pu.user_id
            JOIN Doctor d ON lr.doctor_id=d.doctor_id JOIN Users du ON d.user_id=du.user_id
            ORDER BY lr.test_date DESC
        """)
    reports = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('lab_reports.html', reports=reports)

@app.route('/lab/add', methods=['GET', 'POST'])
@login_required
@role_required('doctor', 'admin')
def add_lab_report():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            cursor.execute("""
                INSERT INTO LabReport (patient_id, doctor_id, test_name, result, normal_range, status, test_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (request.form['patient_id'], request.form['doctor_id'],
                  request.form['test_name'], request.form['result'],
                  request.form['normal_range'], request.form['status'],
                  request.form['test_date'], request.form['notes']))
            db.commit()
            flash('Lab report added!', 'success')
            return redirect(url_for('lab_reports'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    cursor.execute("""
        SELECT p.patient_id, u.name FROM Patient p JOIN Users u ON p.user_id=u.user_id ORDER BY u.name
    """)
    patients = cursor.fetchall()

    if session['role'] == 'doctor':
        doctor_id = session.get('doctor_id')
    else:
        cursor.execute("""
            SELECT d.doctor_id, u.name FROM Doctor d JOIN Users u ON d.user_id=u.user_id
        """)
        doctors = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('add_lab_report.html', patients=patients, doctors=doctors, doctor_id=None)

    cursor.close()
    db.close()
    return render_template('add_lab_report.html', patients=patients, doctor_id=doctor_id)

# ============================================
# BILLING
# ============================================
@app.route('/billing')
@login_required
def billing():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    role = session['role']
    if role == 'patient':
        pid = session.get('patient_id')
        cursor.execute("""
            SELECT b.*, du.name as doctor_name, a.appt_date
            FROM Billing b JOIN Appointment a ON b.appt_id=a.appt_id
            JOIN Doctor d ON a.doctor_id=d.doctor_id JOIN Users du ON d.user_id=du.user_id
            WHERE b.patient_id=%s ORDER BY b.bill_id DESC
        """, (pid,))
    else:
        cursor.execute("""
            SELECT b.*, pu.name as patient_name, du.name as doctor_name, a.appt_date
            FROM Billing b JOIN Patient p ON b.patient_id=p.patient_id
            JOIN Users pu ON p.user_id=pu.user_id
            JOIN Appointment a ON b.appt_id=a.appt_id
            JOIN Doctor d ON a.doctor_id=d.doctor_id JOIN Users du ON d.user_id=du.user_id
            ORDER BY b.bill_id DESC
        """)
    bills = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('billing.html', bills=bills)

@app.route('/billing/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'receptionist')
def add_billing():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            cursor.execute("""
                INSERT INTO Billing (patient_id, appt_id, amount, description)
                VALUES (%s, %s, %s, %s)
            """, (request.form['patient_id'], request.form['appt_id'],
                  request.form['amount'], request.form['description']))
            db.commit()
            flash('Bill added!', 'success')
            return redirect(url_for('billing'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    cursor.execute("""
        SELECT a.appt_id, pu.name as patient_name, p.patient_id, du.name as doctor_name, a.appt_date
        FROM Appointment a JOIN Patient p ON a.patient_id=p.patient_id
        JOIN Users pu ON p.user_id=pu.user_id
        JOIN Doctor d ON a.doctor_id=d.doctor_id JOIN Users du ON d.user_id=du.user_id
        WHERE a.status='Completed'
    """)
    appointments = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('add_billing.html', appointments=appointments)

@app.route('/billing/pay/<int:bill_id>')
@login_required
@role_required('admin', 'receptionist')
def mark_paid(bill_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE Billing SET payment_status='Paid', payment_date=CURDATE() WHERE bill_id=%s", (bill_id,))
    db.commit()
    cursor.close()
    db.close()
    flash('Payment marked as Paid!', 'success')
    return redirect(url_for('billing'))

if __name__ == '__main__':
    app.run(debug=True)
