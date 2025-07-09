from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
Session(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Founas@123',
    'database': 'signin_db'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        flash('Database connection error. Please try again later.', 'danger')
        return None

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if user is admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if user is doctor
def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_doctor'):
            flash('Doctor access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        print(f"✅ User already in session: user_id={session['user_id']}, is_admin={session.get('is_admin')}, is_doctor={session.get('is_doctor')}")
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        elif session.get('is_doctor'):
            return redirect(url_for('doctor_dashboard'))
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"🔑 Login attempt - Username: {username}, Password: {password}")
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'danger')
            return redirect(url_for('login'))
        
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT user_id, username, password, full_name, is_admin, is_doctor 
                    FROM users 
                    WHERE username = %s AND is_active = TRUE
                """, (username,))
                user = cursor.fetchone()
                
                if user:
                    print(f"👤 User found in DB: {user}")
                    if check_password_hash(user['password'], password):
                        print("🔐 Password matches!")
                        
                        # Set session variables
                        session['user_id'] = user['user_id']
                        session['username'] = user['username']
                        session['full_name'] = user['full_name']
                        session['is_admin'] = bool(user['is_admin'])
                        session['is_doctor'] = bool(user['is_doctor'])
                        
                        print(f"📝 Session set - user_id: {session['user_id']}, is_admin: {session['is_admin']}, is_doctor: {session['is_doctor']}")
                        
                        cursor.execute("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user['user_id'],))
                        connection.commit()
                        
                        # Check where the user should be redirected
                        if user['is_admin']:
                            print("🛑 Redirecting to ADMIN dashboard")
                            return redirect(url_for('admin_dashboard'))
                        elif user['is_doctor']:
                            print("🛑 Redirecting to DOCTOR dashboard")
                            return redirect(url_for('doctor_dashboard'))
                        else:
                            print("🛑 Redirecting to USER dashboard")
                            return redirect(url_for('user_dashboard'))
                    else:
                        flash('Invalid username or password', 'danger')
                else:
                    flash('User not found or inactive', 'danger')
        except Exception as e:
            print(f"❌ Login error: {e}")
            flash('An error occurred during login', 'danger')
        finally:
            if connection.is_connected():
                connection.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        
        # Validation
        if not all([username, password, confirm_password, full_name, email, phone]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            return redirect(url_for('register'))
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'danger')
            return redirect(url_for('register'))
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users 
                    (username, password, full_name, email, phone, address, date_of_birth, gender)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    username, 
                    generate_password_hash(password),
                    full_name, 
                    email, 
                    phone, 
                    address, 
                    dob if dob else None, 
                    gender if gender else None
                ))
                connection.commit()
                
                # Auto-login after registration
                user_id = cursor.lastrowid
                session['user_id'] = user_id
                session['username'] = username
                session['full_name'] = full_name
                session['is_admin'] = False
                session['is_doctor'] = False
                session.permanent = True
                
                flash('Registration successful!', 'success')
                return redirect(url_for('user_dashboard'))
        except mysql.connector.IntegrityError as e:
            if 'username' in str(e):
                flash('Username already exists', 'danger')
            elif 'email' in str(e):
                flash('Email already exists', 'danger')
            else:
                flash('Registration error. Please try again.', 'danger')
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred during registration', 'danger')
        finally:
            if connection.is_connected():
                connection.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if session.get('is_doctor'):
        return redirect(url_for('doctor_dashboard'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('home'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            print("Attempting to fetch appointments...")  # Debug
            cursor.execute("""
                SELECT a.*, d.specialization, 
                u.full_name AS doctor_name
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.doctor_id
                JOIN users u ON d.user_id = u.user_id
                WHERE a.user_id = %s
                ORDER BY a.appointment_date DESC, a.start_time DESC
                LIMIT 5
            """, (session['user_id'],))
            appointments = cursor.fetchall()
            print(f"Found {len(appointments)} appointments")  # Debug
            
            print("Attempting to fetch doctors...")  # Debug
            cursor.execute("""
                SELECT d.*, u.full_name, dep.name AS department_name
                FROM doctors d
                JOIN users u ON d.user_id = u.user_id
                LEFT JOIN departments dep ON d.department_id = dep.department_id
                WHERE u.is_active = TRUE
            """)
            doctors = cursor.fetchall()
            print(f"Found {len(doctors)} doctors")  # Debug
            
            print("Attempting to fetch notifications...")  # Debug
            cursor.execute("""
                SELECT * FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 5
            """, (session['user_id'],))
            notifications = cursor.fetchall()
            print(f"Found {len(notifications)} notifications")  # Debug
            
            return render_template('user_dashboard.html', 
                                appointments=appointments, 
                                doctors=doctors,
                                notifications=notifications,
                                today=datetime.now().date())
    except Exception as e:
        print(f"❌ Dashboard error: {str(e)}")  # More detailed error
        flash(f'Error loading dashboard data: {str(e)}', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('login'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # These queries might fail - add error handling
            cursor.execute("SELECT COUNT(*) AS total_users FROM users")
            total_users = cursor.fetchone()['total_users']
            
            # Add error handling for each query
            cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
            total_doctors = cursor.fetchone()['total_doctors']
            
            cursor.execute("""
                SELECT COUNT(*) AS total_appointments,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'Confirmed' THEN 1 ELSE 0 END) AS confirmed,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed
                FROM appointments
            """)
            appointment_stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT a.*, u.full_name AS patient_name, 
                CONCAT(du.first_name, ' ', du.last_name) AS doctor_name
                FROM appointments a
                JOIN users u ON a.user_id = u.user_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                JOIN users du ON d.user_id = du.user_id
                ORDER BY a.appointment_date DESC, a.start_time DESC
                LIMIT 10
            """)
            appointments = cursor.fetchall()
            
            # Check if all expected variables are available
            required_vars = {
                'total_users': total_users,
                'total_doctors': total_doctors,
                'appointment_stats': appointment_stats,
                'appointments': appointments
            }
            
            if None in required_vars.values():
                flash('Failed to load some dashboard data', 'warning')
            
            return render_template('admin_dashboard.html',
                                total_users=total_users,
                                total_doctors=total_doctors,
                                appointment_stats=appointment_stats,
                                appointments=appointments)
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard', 'danger')
        return redirect(url_for('login'))
    finally:
        if connection.is_connected():
            connection.close()


@app.route('/doctor/dashboard')
@doctor_required
def doctor_dashboard():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('login'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Get doctor ID
            cursor.execute("SELECT doctor_id FROM doctors WHERE user_id = %s", (session['user_id'],))
            doctor = cursor.fetchone()
            if not doctor:
                flash('Doctor profile not found', 'danger')
                return redirect(url_for('login'))
            
            doctor_id = doctor['doctor_id']
            
            # Get today's appointments
            today = datetime.now().date()
            cursor.execute("""
                SELECT a.*, u.full_name AS patient_name
                FROM appointments a
                JOIN users u ON a.user_id = u.user_id
                WHERE a.doctor_id = %s AND a.appointment_date = %s
                ORDER BY a.start_time
            """, (doctor_id, today))
            todays_appointments = cursor.fetchall()
            
            # Get total patients
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) AS total_patients
                FROM appointments
                WHERE doctor_id = %s
            """, (doctor_id,))
            total_patients = cursor.fetchone()['total_patients']
            
            return render_template('doctor_dashboard.html',
                                todays_appointments=todays_appointments,
                                total_patients=total_patients,
                                today=today)
    except Exception as e:
        print(f"Doctor dashboard error: {e}")
        flash('Error loading doctor dashboard', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('login'))

@app.route('/book-appointment', methods=['POST'])
@login_required
def book_appointment():
    if session.get('is_admin') or session.get('is_doctor'):
        flash('Please login as a patient to book appointments', 'danger')
        return redirect(url_for('login'))
    
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_date')
    start_time = request.form.get('start_time')
    reason = request.form.get('reason', '').strip()
    
    if not all([doctor_id, appointment_date, start_time]):
        flash('Please fill all required fields', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time, '%H:%M').time()
    except ValueError:
        flash('Invalid date or time format', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Calculate end time (30 minute slots)
    end_time = (datetime.combine(datetime.min, start_time) + timedelta(minutes=30)).time()
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        with connection.cursor() as cursor:
            # Check for existing appointment at same time
            cursor.execute("""
                SELECT appointment_id FROM appointments
                WHERE doctor_id = %s AND appointment_date = %s 
                AND ((start_time <= %s AND end_time > %s) OR (start_time < %s AND end_time >= %s))
            """, (doctor_id, appointment_date, start_time, start_time, end_time, end_time))
            if cursor.fetchone():
                flash('The selected time slot is already booked. Please choose another time.', 'danger')
                return redirect(url_for('user_dashboard'))
            
            # Create appointment
            cursor.execute("""
                INSERT INTO appointments 
                (user_id, doctor_id, appointment_date, start_time, end_time, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session['user_id'], doctor_id, appointment_date, start_time, end_time, reason))
            
            # Create notification
            cursor.execute("""
                SELECT full_name FROM users WHERE user_id = %s
            """, (session['user_id'],))
            patient = cursor.fetchone()
            
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (%s, 'Appointment Booked', 
                CONCAT('Your appointment with Dr. ', 
                (SELECT full_name FROM users WHERE user_id = 
                (SELECT user_id FROM doctors WHERE doctor_id = %s)), 
                ' on ', %s, ' at ', %s, ' has been booked.'))
            """, (session['user_id'], doctor_id, appointment_date.strftime('%b %d, %Y'), start_time.strftime('%I:%M %p')))
            
            connection.commit()
            flash('Appointment booked successfully!', 'success')
    except Exception as e:
        print(f"Booking error: {e}")
        flash('Error booking appointment', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('user_dashboard'))

@app.route('/cancel-appointment/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Check if user owns the appointment or is admin/doctor
            if session.get('is_admin'):
                cursor.execute("""
                    SELECT user_id FROM appointments 
                    WHERE appointment_id = %s
                """, (appointment_id,))
            elif session.get('is_doctor'):
                cursor.execute("""
                    SELECT a.user_id 
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    WHERE a.appointment_id = %s AND d.user_id = %s
                """, (appointment_id, session['user_id']))
            else:
                cursor.execute("""
                    SELECT user_id FROM appointments 
                    WHERE appointment_id = %s AND user_id = %s
                """, (appointment_id, session['user_id']))
            
            appointment = cursor.fetchone()
            
            if not appointment:
                flash('Appointment not found or access denied', 'danger')
                return redirect(url_for('user_dashboard' if not session.get('is_admin') and not session.get('is_doctor') else 'admin_dashboard' if session.get('is_admin') else 'doctor_dashboard'))
            
            # Cancel appointment
            cursor.execute("""
                UPDATE appointments 
                SET status = 'Cancelled'
                WHERE appointment_id = %s
            """, (appointment_id,))
            
            # Create notification
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (%s, 'Appointment Cancelled', 
                CONCAT('Your appointment on ', 
                (SELECT appointment_date FROM appointments WHERE appointment_id = %s), 
                ' has been cancelled.'))
            """, (appointment['user_id'], appointment_id))
            
            connection.commit()
            flash('Appointment cancelled', 'info')
    except Exception as e:
        print(f"Cancellation error: {e}")
        flash('Error cancelling appointment', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    elif session.get('is_doctor'):
        return redirect(url_for('doctor_dashboard'))
    return redirect(url_for('user_dashboard'))

@app.route('/complete-appointment/<int:appointment_id>')
@doctor_required
def complete_appointment(appointment_id):
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('doctor_dashboard'))
    
    try:
        with connection.cursor() as cursor:
            # Verify the doctor owns this appointment
            cursor.execute("""
                SELECT a.appointment_id 
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.appointment_id = %s AND d.user_id = %s
            """, (appointment_id, session['user_id']))
            
            if not cursor.fetchone():
                flash('Appointment not found or access denied', 'danger')
                return redirect(url_for('doctor_dashboard'))
            
            # Mark as completed
            cursor.execute("""
                UPDATE appointments 
                SET status = 'Completed'
                WHERE appointment_id = %s
            """, (appointment_id,))
            
            connection.commit()
            flash('Appointment marked as completed', 'success')
    except Exception as e:
        print(f"Completion error: {e}")
        flash('Error completing appointment', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('doctor_dashboard'))

@app.route('/appointments')
@login_required
def view_appointments():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # For doctors, show their appointments
            if session.get('is_doctor'):
                cursor.execute("""
                    SELECT doctor_id FROM doctors WHERE user_id = %s
                """, (session['user_id'],))
                doctor = cursor.fetchone()
                if not doctor:
                    flash('Doctor profile not found', 'danger')
                    return redirect(url_for('login'))
                
                cursor.execute("""
                    SELECT a.*, u.full_name AS patient_name
                    FROM appointments a
                    JOIN users u ON a.user_id = u.user_id
                    WHERE a.doctor_id = %s
                    ORDER BY a.appointment_date DESC, a.start_time DESC
                """, (doctor['doctor_id'],))
            
            # For admins, show all appointments
            elif session.get('is_admin'):
                cursor.execute("""
                    SELECT a.*, u.full_name AS patient_name, 
                    CONCAT(du.first_name, ' ', du.last_name) AS doctor_name
                    FROM appointments a
                    JOIN users u ON a.user_id = u.user_id
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    JOIN users du ON d.user_id = du.user_id
                    ORDER BY a.appointment_date DESC, a.start_time DESC
                """)
            
            # For regular users, show their own appointments
            else:
                cursor.execute("""
                    SELECT a.*, d.specialization, 
                    CONCAT(u.first_name, ' ', u.last_name) AS doctor_name
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    JOIN users u ON d.user_id = u.user_id
                    WHERE a.user_id = %s
                    ORDER BY a.appointment_date DESC, a.start_time DESC
                """, (session['user_id'],))
            
            appointments = cursor.fetchall()
            return render_template('appointments.html', appointments=appointments)
    except Exception as e:
        print(f"Appointments error: {e}")
        flash('Error loading appointments', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('user_dashboard'))

@app.route('/medical-records')
@login_required
def medical_records():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # For doctors, show records they've created
            if session.get('is_doctor'):
                cursor.execute("""
                    SELECT mr.*, u.full_name AS patient_name
                    FROM medical_records mr
                    JOIN users u ON mr.user_id = u.user_id
                    WHERE mr.doctor_id = (
                        SELECT doctor_id FROM doctors WHERE user_id = %s
                    )
                    ORDER BY mr.visit_date DESC
                """, (session['user_id'],))
            
            # For admins, show all records
            elif session.get('is_admin'):
                cursor.execute("""
                    SELECT mr.*, u.full_name AS patient_name, 
                    CONCAT(du.first_name, ' ', du.last_name) AS doctor_name
                    FROM medical_records mr
                    JOIN users u ON mr.user_id = u.user_id
                    JOIN doctors d ON mr.doctor_id = d.doctor_id
                    JOIN users du ON d.user_id = du.user_id
                    ORDER BY mr.visit_date DESC
                """)
            
            # For regular users, show their own records
            else:
                cursor.execute("""
                    SELECT mr.*, d.specialization, 
                    CONCAT(u.first_name, ' ', u.last_name) AS doctor_name
                    FROM medical_records mr
                    JOIN doctors d ON mr.doctor_id = d.doctor_id
                    JOIN users u ON d.user_id = u.user_id
                    WHERE mr.user_id = %s
                    ORDER BY mr.visit_date DESC
                """, (session['user_id'],))
            
            records = cursor.fetchall()
            return render_template('medical_records.html', records=records)
    except Exception as e:
        print(f"Medical records error: {e}")
        flash('Error loading medical records', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('user_dashboard'))

@app.route('/add-medical-record', methods=['GET', 'POST'])
@login_required
def add_medical_record():
    if not (session.get('is_doctor') or session.get('is_admin')):
        flash('Doctor or admin access required', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        diagnosis = request.form.get('diagnosis', '').strip()
        treatment = request.form.get('treatment', '').strip()
        prescription = request.form.get('prescription', '').strip()
        notes = request.form.get('notes', '').strip()
        follow_up_date = request.form.get('follow_up_date', '')
        
        if not user_id or not diagnosis:
            flash('Patient and diagnosis are required', 'danger')
            return redirect(url_for('add_medical_record'))
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'danger')
            return redirect(url_for('doctor_dashboard'))
        
        try:
            with connection.cursor() as cursor:
                # Get doctor ID
                cursor.execute("""
                    SELECT doctor_id FROM doctors WHERE user_id = %s
                """, (session['user_id'],))
                doctor = cursor.fetchone()
                
                if not doctor:
                    flash('Doctor profile not found', 'danger')
                    return redirect(url_for('doctor_dashboard'))
                
                # Create medical record
                cursor.execute("""
                    INSERT INTO medical_records 
                    (user_id, doctor_id, visit_date, diagnosis, treatment, 
                    prescription, notes, follow_up_date)
                    VALUES (%s, %s, CURDATE(), %s, %s, %s, %s, %s)
                """, (
                    user_id, doctor['doctor_id'], diagnosis, treatment, 
                    prescription, notes, follow_up_date if follow_up_date else None
                ))
                
                connection.commit()
                flash('Medical record added successfully', 'success')
                return redirect(url_for('medical_records'))
        except Exception as e:
            print(f"Medical record error: {e}")
            flash('Error adding medical record', 'danger')
        finally:
            if connection.is_connected():
                connection.close()
    
    # For GET request - show form
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('doctor_dashboard'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT user_id, full_name FROM users WHERE is_doctor = FALSE AND is_admin = FALSE")
            patients = cursor.fetchall()
            return render_template('add_medical_record.html', patients=patients)
    except Exception as e:
        print(f"Patient list error: {e}")
        flash('Error loading patient list', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('doctor_dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        blood_type = request.form.get('blood_type', '')
        
        if not all([full_name, email, phone]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('user_profile'))
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'danger')
            return redirect(url_for('user_profile'))
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET full_name = %s, email = %s, phone = %s, 
                        address = %s, date_of_birth = %s, 
                        gender = %s, blood_type = %s
                    WHERE user_id = %s
                """, (
                    full_name, email, phone, address, 
                    dob if dob else None, gender if gender else None, 
                    blood_type if blood_type else None, session['user_id']
                ))
                connection.commit()
                
                # Update session
                session['full_name'] = full_name
                flash('Profile updated successfully', 'success')
        except mysql.connector.IntegrityError as e:
            if 'email' in str(e):
                flash('Email already exists', 'danger')
            else:
                flash('Profile update error', 'danger')
        except Exception as e:
            print(f"Profile update error: {e}")
            flash('Error updating profile', 'danger')
        finally:
            if connection.is_connected():
                connection.close()
        
        return redirect(url_for('user_profile'))
    
    # GET request - show profile
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT * FROM users 
                WHERE user_id = %s
            """, (session['user_id'],))
            user = cursor.fetchone()
            
            if session.get('is_doctor'):
                cursor.execute("""
                    SELECT * FROM doctors 
                    WHERE user_id = %s
                """, (session['user_id'],))
                doctor_info = cursor.fetchone()
            else:
                doctor_info = None
            
            return render_template('profile.html', user=user, doctor_info=doctor_info)
    except Exception as e:
        print(f"Profile error: {e}")
        flash('Error loading profile', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('user_dashboard'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not all([current_password, new_password, confirm_password]):
        flash('Please fill all password fields', 'danger')
        return redirect(url_for('user_profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('user_profile'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters', 'danger')
        return redirect(url_for('user_profile'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('user_profile'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Verify current password
            cursor.execute("""
                SELECT password FROM users 
                WHERE user_id = %s
            """, (session['user_id'],))
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user['password'], current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('user_profile'))
            
            # Update password
            cursor.execute("""
                UPDATE users 
                SET password = %s
                WHERE user_id = %s
            """, (generate_password_hash(new_password), session['user_id']))
            connection.commit()
            
            flash('Password changed successfully', 'success')
    except Exception as e:
        print(f"Password change error: {e}")
        flash('Error changing password', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('user_profile'))

@app.route('/api/doctor-availability/<int:doctor_id>')
def doctor_availability(doctor_id):
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    try:
        date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Get doctor's working hours
            cursor.execute("""
                SELECT available_days, available_time 
                FROM doctors 
                WHERE doctor_id = %s
            """, (doctor_id,))
            doctor = cursor.fetchone()
            
            if not doctor:
                return jsonify({'error': 'Doctor not found'}), 404
            
            # Parse available time (format: "HH:MM-HH:MM")
            start_time_str, end_time_str = doctor['available_time'].split('-')
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Generate 30-minute slots
            slots = []
            current_time = datetime.combine(date, start_time)
            end_datetime = datetime.combine(date, end_time)
            
            while current_time + timedelta(minutes=30) <= end_datetime:
                slots.append(current_time.time().strftime('%H:%M'))
                current_time += timedelta(minutes=30)
            
            # Remove booked slots
            cursor.execute("""
                SELECT start_time FROM appointments
                WHERE doctor_id = %s AND appointment_date = %s
                AND status IN ('Pending', 'Confirmed')
            """, (doctor_id, date))
            booked_slots = [row['start_time'].strftime('%H:%M') for row in cursor.fetchall()]
            
            available_slots = [slot for slot in slots if slot not in booked_slots]
            
            return jsonify({
                'date': date.strftime('%Y-%m-%d'),
                'available_slots': available_slots
            })
    except Exception as e:
        print(f"Availability error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            connection.close()

@app.route('/notifications')
@login_required
def notifications():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Get all notifications
            cursor.execute("""
                SELECT * FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (session['user_id'],))
            notifications = cursor.fetchall()
            
            # Mark all as read
            cursor.execute("""
                UPDATE notifications
                SET is_read = TRUE
                WHERE user_id = %s AND is_read = FALSE
            """, (session['user_id'],))
            connection.commit()
            
            return render_template('notifications.html', notifications=notifications)
    except Exception as e:
        print(f"Notifications error: {e}")
        flash('Error loading notifications', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('user_dashboard'))

@app.route('/admin/users')
@admin_required
def manage_users():
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT user_id, username, full_name, email, phone, 
                is_active, is_admin, is_doctor, last_login
                FROM users
                ORDER BY is_admin DESC, is_doctor DESC, full_name
            """)
            users = cursor.fetchall()
            return render_template('manage_users.html', users=users)
    except Exception as e:
        print(f"Users list error: {e}")
        flash('Error loading users list', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-user-status/<int:user_id>')
@admin_required
def toggle_user_status(user_id):
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('manage_users'))
@app.route('/admin/toggle-user-status/<int:user_id>')
@admin_required
def toggle_user_status_admin(user_id):
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        with connection.cursor() as cursor:
            # Toggle user status
            cursor.execute("""
                UPDATE users 
                SET is_active = NOT is_active 
                WHERE user_id = %s
            """, (user_id,))
            connection.commit()
            flash('User  status updated successfully', 'success')
    except Exception as e:
        print(f"Toggle user status error: {e}")
        flash('Error updating user status', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('manage_users'))

@app.route('/admin/delete-user/<int:user_id>')
@admin_required
def delete_user(user_id):
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        with connection.cursor() as cursor:
            # Delete user
            cursor.execute("""
               DELETE FROM users 
                WHERE user_id = %s
            """, (user_id,))
            connection.commit()
            flash('User  deleted successfully', 'success')
    except Exception as e:
        print(f"Delete user error: {e}")
        flash('Error deleting user', 'danger')
    finally:
        if connection.is_connected():
            connection.close()
    
    return redirect(url_for('manage_users'))
if __name__ == '__main__':
    app.run(debug=True)
