from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, time as dtime
import mysql.connector
from mysql.connector import Error
import os
import logging
from functools import wraps
import hashlib

app = Flask(__name__)
# Use a stable secret key from env in production; fallback to random for development
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
Session(app)

def safe_time(obj):
    if obj is None:
        return "—"
    if isinstance(obj, str):
        return obj[:5]
    if isinstance(obj, dtime):
        return obj.strftime('%I:%M %p')
    if isinstance(obj, timedelta):
        total = int(obj.total_seconds())
        h = total // 3600
        m = (total % 3600) // 60
        return dtime(h, m).strftime('%I:%M %p')
    try:
        return obj.strftime('%I:%M %p')
    except:
        return str(obj)[:8]

app.jinja_env.filters['safe_time'] = safe_time

# REGISTER FILTER — NOW app EXISTS!
app.jinja_env.filters['safe_time'] = safe_time

# Basic logging
logging.basicConfig(level=logging.INFO)

# Database configuration
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'Founas@123'),
    'database': os.environ.get('DB_NAME', 'HospitalManagementSystem')
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        logging.exception("Error connecting to MySQL")
        return None


# ----------------- DECORATORS -----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'danger')
            return redirect(url_for('login'))
        if session.get('user_type') != 'admin':
            flash('Access Denied: Admin Only', 'danger')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'doctor':
            flash('Doctor access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- ROUTES -----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'danger')
            return redirect(url_for('login'))

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT user_id, username, password_hash, user_type 
                FROM Users 
                WHERE username = %s AND is_active = TRUE
            """, (username,))
            user = cursor.fetchone()

            password_ok = False
            if user:
                stored_hash = user.get('password_hash') or ''
                # Prefer Werkzeug salted hashes
                if stored_hash and check_password_hash(stored_hash, password):
                    password_ok = True
                else:
                    # Backwards compatibility: accept legacy SHA256 hex (length 64)
                    if stored_hash and len(stored_hash) == 64:
                        if hashlib.sha256(password.encode()).hexdigest() == stored_hash:
                            password_ok = True
                            # Migrate to Werkzeug hash for future logins
                            try:
                                with conn.cursor() as update_cursor:
                                    update_cursor.execute(
                                        """
                                        UPDATE Users SET password_hash = %s WHERE user_id = %s
                                        """,
                                        (generate_password_hash(password), user['user_id'])
                                    )
                                    conn.commit()
                            except Exception:
                                logging.exception("Failed to migrate legacy SHA256 password")

            if password_ok:
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                session['is_admin'] = user['user_type'] == 'admin'
                session['is_doctor'] = user['user_type'] == 'doctor'

                if user['user_type'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['user_type'] == 'doctor':
                    return redirect(url_for('doctor_dashboard'))
                else:
                    # Regular users go to the generic user dashboard
                    return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid username or password', 'danger')

        except Exception as e:
            # Log full traceback and show message for development debugging
            logging.exception("Login error")
            flash(f'Error during login: {e}', 'danger')
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                logging.exception("Error closing DB connection after login")

    return render_template('login.html')

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'danger')
            return redirect(url_for('register'))

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM Users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))

            cursor.execute("""
                INSERT INTO Users (username, password_hash, email, user_type)
                VALUES (%s, %s, %s, 'patient')
            """, (username, generate_password_hash(password), email))
            conn.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"❌ Registration error: {e}")
            flash('Error during registration', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if session.get('is_admin'): return redirect(url_for('admin_dashboard'))
    if session.get('is_doctor'): return redirect(url_for('doctor_dashboard'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'danger')
        return redirect(url_for('home'))

    try:
        with conn.cursor(dictionary=True) as cur:
            # 1. Appointments
            cur.execute("""
                SELECT 
                    a.*,
                    d.specialization,
                    COALESCE(u.full_name, u.username, CONCAT('Dr. ', u.username), 'Dr. Unknown') AS doctor_name
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.doctor_id
                JOIN users u ON d.user_id = u.user_id
                WHERE a.user_id = %s
                ORDER BY a.appointment_date DESC, a.start_time DESC 
                LIMIT 10
            """, (session['user_id'],))
            appointments = cur.fetchall()

            # 2. Doctors
            # === 2. Fetch Doctors (FIXED - ALWAYS SHOWS NAME) ===
            cur.execute("""
                SELECT 
                    d.doctor_id,
                    d.specialization,
                    COALESCE(u.full_name, u.username, 'Dr. Unknown') AS display_name,
                    u.email, u.phone,
                    dep.name AS department_name
                FROM doctors d
                JOIN users u ON d.user_id = u.user_id
                LEFT JOIN departments dep ON d.department_id = dep.department_id
                WHERE u.is_active = TRUE
                LIMIT 50
            """)
            doctors = cur.fetchall()

            # 3. Notifications
            cur.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (session['user_id'],))
            notifications = cur.fetchall()

            # 4. Departments
            cur.execute("SELECT department_id, name FROM departments ORDER BY name")
            departments = cur.fetchall()

            # === SERVER-SIDE TIME SLOTS (NO JS) ===
            doctor_id = request.args.get('doctor_id')
            appointment_date = request.args.get('appointment_date')
            selected_doctor = None
            selected_date = None
            available_slots = []

            if doctor_id and appointment_date:
                try:
                    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                    selected_date = appointment_date
                    weekday = date_obj.strftime('%A').lower()

                    # Get doctor
                    cur.execute("""
                        SELECT 
                            d.*,
                            COALESCE(u.full_name, u.username, 'Dr. Unknown') AS display_name,
                            u.email,
                            d.specialization
                        FROM doctors d
                        JOIN users u ON d.user_id = u.user_id
                        WHERE d.doctor_id = %s
                    """, (doctor_id,))
                    selected_doctor = cur.fetchone()

                    if not selected_doctor:
                        available_slots = []
                    else:
                        slots = set()

                        # METHOD 1: Use available_time (e.g., "09:00-17:00")
                        avail = selected_doctor.get('available_time', '').strip()
                        if avail and '-' in avail:
                            try:
                                start_str, end_str = avail.split('-', 1)
                                start = datetime.strptime(start_str.strip(), '%H:%M').time()
                                end = datetime.strptime(end_str.strip(), '%H:%M').time()
                                current = datetime.combine(date_obj, start)
                                end_dt = datetime.combine(date_obj, end)
                                while current < end_dt:
                                    slots.add(current.strftime('%H:%M'))
                                    current += timedelta(minutes=30)
                            except:
                                pass  # skip bad format

                        # METHOD 2: Use doctor_schedules table
                        cur.execute("""
                            SELECT start_time, end_time 
                            FROM doctor_schedules 
                            WHERE doctor_id = %s AND LOWER(day_of_week) = %s
                        """, (doctor_id, weekday))
                        rows = cur.fetchall()

                        for row in rows:
                            try:
                                st = row['start_time']
                                et = row['end_time']

                                if isinstance(st, str):
                                    st = datetime.strptime(st[:5], '%H:%M').time()
                                if isinstance(et, str):
                                    et = datetime.strptime(et[:5], '%H:%M').time()

                                current = datetime.combine(date_obj, st)
                                end_dt = datetime.combine(date_obj, et)

                                while current < end_dt:
                                    slots.add(current.strftime('%H:%M'))
                                    current += timedelta(minutes=30)
                            except:
                                continue

                        # METHOD 3: FALLBACK — Generate 9 AM to 5 PM if nothing else works
                        if not slots:
                            start = datetime.combine(date_obj, time(9, 0))
                            end = datetime.combine(date_obj, time(17, 0))
                            while start < end:
                                slots.add(start.strftime('%H:%M'))
                                start += timedelta(minutes=30)

                        # Remove booked slots
                        cur.execute("""
                            SELECT start_time FROM appointments
                            WHERE doctor_id = %s AND appointment_date = %s
                            AND status IN ('Pending', 'Confirmed')
                        """, (doctor_id, date_obj))
                        booked = {
                            r['start_time'].strftime('%H:%M') if hasattr(r['start_time'], 'strftime')
                            else str(r['start_time'])[:5]
                            for r in cur.fetchall()
                        }

                        available_slots = sorted([s for s in slots if s not in booked])

                except Exception as e:
                    logging.error(f"Time slot error: {e}")
                    available_slots = ["09:00", "09:30", "10:00", "10:30", "11:00"]  # fallback

            return render_template('user_dashboard.html',
                                   appointments=appointments,
                                   doctors=doctors,
                                   notifications=notifications,
                                   departments=departments,
                                   today=datetime.now().date(),
                                   selected_doctor=selected_doctor,
                                   selected_date=selected_date,
                                   available_slots=available_slots or [])

    except Exception as e:
        logging.exception("Dashboard error")
        flash('Error loading page', 'danger')

    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed', 'danger')
        return redirect(url_for('login'))

    try:
        with conn.cursor(dictionary=True) as cur:
            # STATS
            cur.execute("SELECT COUNT(*) AS total FROM users WHERE user_type = 'patient'")
            total_patients = cur.fetchone()['total'] or 0

            cur.execute("SELECT COUNT(*) AS total FROM doctors")
            total_doctors = cur.fetchone()['total'] or 0

            cur.execute("SELECT COUNT(*) AS total FROM appointments")
            total_appointments = cur.fetchone()['total'] or 0

            cur.execute("SELECT COUNT(*) AS total FROM appointments WHERE status = 'Pending'")
            pending_appointments = cur.fetchone()['total'] or 0

            # ALL APPOINTMENTS WITH CORRECT NAMES (FIXED!)
            cur.execute("""
                SELECT 
                    a.appointment_id,
                    a.appointment_date,
                    a.start_time,
                    a.reason,
                    a.status,
                    COALESCE(p.full_name, p.username, 'Unknown Patient') AS patient_name,
                    COALESCE(d.full_name, d.username, 'Dr. Unknown') AS doctor_name,
                    doc.specialization
                FROM appointments a
                LEFT JOIN users p ON a.user_id = p.user_id
                LEFT JOIN doctors doc ON a.doctor_id = doc.doctor_id
                LEFT JOIN users d ON doc.user_id = d.user_id
                ORDER BY a.appointment_date DESC, a.start_time DESC
                LIMIT 50
            """)
            recent_appointments = cur.fetchall()

            return render_template('admin_dashboard.html',
                                   total_patients=total_patients,
                                   total_doctors=total_doctors,
                                   total_appointments=total_appointments,
                                   pending_appointments=pending_appointments,
                                   recent_appointments=recent_appointments)

    except Exception as e:
        logging.error(f"Admin Dashboard Error: {e}")
        flash(f'Dashboard error: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/doctor/dashboard')
@login_required
@doctor_required
def doctor_dashboard():
    connection = get_db_connection()
    
    # DEFAULT SAFE VALUES
    doctor = {'doctor_name': 'Doctor', 'specialization': 'General'}
    today_appointments = []
    upcoming_appointments = []
    today = datetime.now().date()

    if not connection:
        flash('Cannot connect to database. Showing offline mode.', 'info')
        return render_template('doctor_dashboard.html',
                               doctor=doctor,
                               today_appointments=today_appointments,
                               upcoming_appointments=upcoming_appointments,
                               today=today)

    try:
        with connection.cursor(dictionary=True) as cursor:
            # 1. Get doctor info
            cursor.execute("""
                SELECT d.doctor_id, 
                       COALESCE(u.full_name, u.username, 'Dr. Unknown') AS doctor_name,
                       COALESCE(d.specialization, 'General') AS specialization
                FROM doctors d
                JOIN users u ON d.user_id = u.user_id
                WHERE u.user_id = %s
            """, (session['user_id'],))
            doctor_result = cursor.fetchone()
            
            if not doctor_result:
                flash('Profile incomplete. Please contact admin.', 'warning')
            else:
                doctor = doctor_result

            doctor_id = doctor.get('doctor_id')
            if not doctor_id:
                return render_template('doctor_dashboard.html',
                                       doctor=doctor,
                                       today_appointments=today_appointments,
                                       upcoming_appointments=upcoming_appointments,
                                       today=today)

            # 2. Today's appointments
            cursor.execute("""
                SELECT 
                    a.appointment_id,
                    a.start_time,
                    a.reason,
                    a.status,
                    COALESCE(u.full_name, u.username, 'Patient') AS patient_name,
                    COALESCE(u.phone, '—') AS phone
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.user_id
                WHERE a.doctor_id = %s AND a.appointment_date = %s
                ORDER BY a.start_time
            """, (doctor_id, today))
            today_appointments = cursor.fetchall()

            # 3. Upcoming (next 10 days)
            cursor.execute("""
                SELECT 
                    a.appointment_date,
                    a.start_time,
                    a.reason,
                    a.status,
                    COALESCE(u.full_name, u.username, 'Patient') AS patient_name
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.user_id
                WHERE a.doctor_id = %s 
                  AND a.appointment_date >= %s 
                  AND a.appointment_date <= %s
                ORDER BY a.appointment_date, a.start_time
                LIMIT 15
            """, (doctor_id, today, today + timedelta(days=10)))
            upcoming_appointments = cursor.fetchall()

        # SUCCESS — NO ERRORS
        flash('Dashboard loaded successfully', 'success')  # Optional: remove if too chatty

    except mysql.connector.Error as db_err:
        # ONLY REAL DB ERRORS
        logging.error(f"DB Error in doctor dashboard: {db_err}")
        flash('Database temporarily unavailable. Try again in 1 minute.', 'danger')
    except Exception as e:
        # ONLY UNEXPECTED CRASHES
        logging.exception("CRITICAL: Doctor dashboard crashed")
        flash('System error. Developers notified.', 'danger')
    finally:
        if connection and connection.is_connected():
            connection.close()

    return render_template('doctor_dashboard.html',
                           doctor=doctor,
                           today_appointments=today_appointments or [],
                           upcoming_appointments=upcoming_appointments or [],
                           today=today)

@app.route('/doctor/complete/<int:id>')
@doctor_required
def doctor_complete(id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE appointments SET status='Completed' WHERE appointment_id=%s AND doctor_id IN (SELECT doctor_id FROM doctors WHERE user_id=%s)", 
                           (id, session['user_id']))
            conn.commit()
            flash('Marked as Completed', 'success')
        except Exception as e:
            logging.error(f"Complete failed: {e}")
            flash('Failed to update', 'danger')
        finally:
            conn.close()
    return redirect(url_for('doctor_dashboard'))


@app.route('/doctor/<int:doctor_id>/profile')
@login_required
def doctor_profile(doctor_id):
    """Return JSON with doctor details and schedules for client-side modal loading."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'database connection error'}), 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT d.*, u.full_name, u.phone AS phone_number, dep.name AS department_name, u.email
                FROM doctors d
                JOIN users u ON d.user_id = u.user_id
                LEFT JOIN departments dep ON d.department_id = dep.department_id
                WHERE d.doctor_id = %s
            """, (doctor_id,))
            doc = cursor.fetchone()
            if not doc:
                return jsonify({'error': 'not found'}), 404

            cursor.execute("SELECT day_of_week, start_time, end_time FROM doctor_schedules WHERE doctor_id = %s ORDER BY FIELD(day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), start_time", (doctor_id,))
            scheds = cursor.fetchall()
            doc['schedules'] = scheds or []

            # Convert any non-serializable types if present (mysql returns time as time objects)
            availability_lines = []
            for s in doc['schedules']:
                # stringify time objects if needed (MySQL returns datetime.time)
                st = s.get('start_time')
                et = s.get('end_time')
                if hasattr(st, 'strftime'):
                    s['start_time'] = st.strftime('%H:%M')
                else:
                    s['start_time'] = str(st) if st is not None else ''
                if hasattr(et, 'strftime'):
                    s['end_time'] = et.strftime('%H:%M')
                else:
                    s['end_time'] = str(et) if et is not None else ''

                # build a readable availability line like 'Monday → 09:00–13:00'
                dow = s.get('day_of_week') or ''
                if dow and s.get('start_time') and s.get('end_time'):
                    availability_lines.append(f"{dow} → {s['start_time']}–{s['end_time']}")

            # attach a friendly availability representation
            doc['availability_lines'] = availability_lines

            return jsonify(doc)
    except Exception:
        logging.exception('Failed to load doctor profile')
        return jsonify({'error': 'server error'}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_date')
    start_time = request.form.get('start_time')
    reason = request.form.get('reason', '').strip()

    if not all([doctor_id, appointment_date, start_time, reason]):
        flash('All fields are required', 'danger')
        return redirect(url_for('user_dashboard'))

    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('user_dashboard'))

    try:
        with conn.cursor(dictionary=True) as cur:
            # FIRST: Get doctor name (to save it!)
            cur.execute("""
                SELECT COALESCE(u.full_name, u.username, 'Dr. Unknown') AS doctor_name
                FROM doctors d
                JOIN users u ON d.user_id = u.user_id
                WHERE d.doctor_id = %s
            """, (doctor_id,))
            doc = cur.fetchone()
            doctor_name = doc['doctor_name'] if doc else 'Dr. Unknown'

            # SECOND: Check if slot is free
            cur.execute("""
                SELECT appointment_id FROM appointments
                WHERE doctor_id = %s AND appointment_date = %s AND start_time = %s
                AND status IN ('Pending', 'Confirmed')
            """, (doctor_id, appointment_date, start_time))
            if cur.fetchone():
                flash('This time slot is no longer available', 'danger')
                return redirect(url_for('user_dashboard') + f'?doctor_id={doctor_id}&appointment_date={appointment_date}')

            # THIRD: BOOK + SAVE DOCTOR NAME
            cur.execute("""
                INSERT INTO appointments 
                (user_id, doctor_id, appointment_date, start_time, reason, status, doctor_name)
                VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
            """, (session['user_id'], doctor_id, appointment_date, start_time, reason, doctor_name))
            
        conn.commit()
        flash('Appointment booked successfully!', 'success')
    except Exception as e:
        logging.exception("Booking failed")
        flash('Failed to book appointment', 'danger')
    
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
def view_appointment():
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
                SELECT password_hash FROM Users 
                WHERE user_id = %s
            """, (session['user_id'],))
            user = cursor.fetchone()

            if not user or not check_password_hash(user.get('password_hash', ''), current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('user_profile'))

            # Update password_hash
            cursor.execute("""
                UPDATE Users 
                SET password_hash = %s
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
# ADMIN: APPROVE
@app.route('/admin/approve/<int:id>')
@admin_required
def admin_approve(id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE appointments SET status='Confirmed' WHERE appointment_id=%s", (id,))
    conn.commit()
    flash('Appointment APPROVED', 'success')
    return redirect(url_for('admin_dashboard'))

# ADMIN: CANCEL
@app.route('/admin/cancel/<int:id>')
@admin_required
def admin_cancel(id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE appointments SET status='Cancelled' WHERE appointment_id=%s", (id,))
    conn.commit()
    flash('Appointment CANCELLED', 'warning')
    return redirect(url_for('admin_dashboard'))

# ADMIN: RESCHEDULE
@app.route('/admin/reschedule/<int:id>', methods=['POST'])
@admin_required
def admin_reschedule(id):
    new_date = request.form['new_date']
    new_time = request.form['new_time']
    new_reason = request.form['new_reason']
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE appointments 
            SET appointment_date=%s, start_time=%s, reason=%s, status='Confirmed'
            WHERE appointment_id=%s
        """, (new_date, new_time, new_reason, id))
    conn.commit()
    flash('Appointment RESCHEDULED', 'info')
    return redirect(url_for('admin_dashboard'))

# ADMIN: DELETE FOREVER
@app.route('/admin/delete/<int:id>')
@admin_required
def admin_delete(id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM appointments WHERE appointment_id=%s", (id,))
    conn.commit()
    flash('Appointment DELETED FOREVER', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-user-status/<int:user_id>')
@admin_required
def toggle_user_status(user_id):
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        with connection.cursor() as cursor:
            # Toggle user status
            cursor.execute("""
                UPDATE Users 
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
