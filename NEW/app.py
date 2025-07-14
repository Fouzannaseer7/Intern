from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timedelta
import os
from functools import wraps
from mysql.connector import Error as DBError
from contextlib import closing

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=30)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Founas@123',
    'database': 'HospitalManagementSystem'
}

# ======================
#  HELPER FUNCTIONS
# ======================

def get_db_connection():
    """Establish database connection with error handling"""
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            print("✅ Database connection successful")
            return conn
        print("❌ Database connection failed")
        return None
    except DBError as err:
        print(f"❌ Database connection error: {err}")
        return None

def execute_query(query, params=None, fetch=False, lastrow=False):
    """
    Safe database query execution
    Returns:
    - For SELECT: List of dicts if fetch='all', single dict if fetch='one'
    - For INSERT/UPDATE/DELETE: True if success, None if error
    - For lastrow: Returns lastrowid if success
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with closing(conn.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params or ())
            
            if fetch:
                return cursor.fetchall() if fetch == 'all' else cursor.fetchone()
            if lastrow:
                return cursor.lastrowid
            
            conn.commit()
            return True
            
    except DBError as err:
        print(f"Database error: {err}")
        conn.rollback()
        return None
    finally:
        if conn.is_connected():
            conn.close()

def login_required(role=None):
    """Decorator to check if user is logged in and has the right role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('login'))
            
            if role and session.get('user_type') != role:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ======================
#  CORE ROUTES
# ======================

@app.before_request
def before_request():
    """Refresh session lifetime with each request"""
    session.permanent = True

@app.route('/')
def home():
    if 'user_id' in session:
        user_type = session.get('user_type')
        print("🔐 User Type in Session:", user_type)

        if user_type == 'patient':
            return redirect(url_for('patient_dashboard'))
        elif user_type == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        elif user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            print("❌ Unknown user_type:", user_type)
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = execute_query(
            "SELECT * FROM Users WHERE username = %s AND password_hash = SHA2(%s, 256)",
            (username, password),
            fetch='one'
        )

        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return redirect(url_for('login'))

        user = execute_query(
            "SELECT * FROM Users WHERE username = %s AND is_active = TRUE",
            (username,),
            fetch='one'
        )

        

        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']

            flash('Login successful!', 'success')

            # ✅ Role-based redirect
            if user['user_type'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['user_type'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))

        flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout route that clears the session"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Patient registration route with comprehensive error handling"""
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            # Get and validate form data
            form_data = {
                'username': request.form.get('username', '').strip(),
                'email': request.form.get('email', '').strip().lower(),
                'password': request.form.get('password', '').strip(),
                'confirm_password': request.form.get('confirm_password', '').strip(),
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'date_of_birth': request.form.get('date_of_birth'),
                'gender': request.form.get('gender'),
                'phone': request.form.get('phone', '').strip()
            }

            # Validate required fields
            errors = []
            required_fields = ['username', 'email', 'password', 'confirm_password',
                              'first_name', 'last_name', 'date_of_birth', 'gender']
            
            for field in required_fields:
                if not form_data[field]:
                    errors.append(f"{field.replace('_', ' ').title()} is required")

            # Additional validations
            if len(form_data['username']) < 4:
                errors.append("Username must be at least 4 characters")
            
            if len(form_data['password']) < 8:
                errors.append("Password must be at least 8 characters")
            
            if form_data['password'] != form_data['confirm_password']:
                errors.append("Passwords do not match")
            
            if '@' not in form_data['email']:
                errors.append("Invalid email address")
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('register.html', form_data=form_data)

            # Check for existing user
            existing = execute_query(
                "SELECT username, email FROM Users WHERE username = %s OR email = %s",
                (form_data['username'], form_data['email']),
                fetch='one'
            )
            
            if existing:
                if existing['username'] == form_data['username']:
                    flash('Username already exists', 'danger')
                if existing['email'] == form_data['email']:
                    flash('Email already registered', 'danger')
                return render_template('register.html', form_data=form_data)

            # Start transaction
            conn = get_db_connection()
            if not conn:
                flash('Database connection error', 'danger')
                return render_template('register.html', form_data=form_data)

            try:
                cursor = conn.cursor(dictionary=True)
                
                # Create user account
                hashed_pw = generate_password_hash(form_data['password'])
                cursor.execute(
                    """INSERT INTO Users (username, password_hash, email, user_type)
                       VALUES (%s, %s, %s, 'patient')""",
                    (form_data['username'], hashed_pw, form_data['email'])
                )
                user_id = cursor.lastrowid
                
                if not user_id:
                    raise Exception("Failed to create user account")

                # Create patient record
                cursor.execute(
                    """INSERT INTO Patients (user_id, first_name, last_name, date_of_birth, gender, phone_number)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, form_data['first_name'], form_data['last_name'], 
                     form_data['date_of_birth'], form_data['gender'], form_data['phone'])
                )
                
                conn.commit()
                flash('Registration successful! Please login', 'success')
                return redirect(url_for('login'))

            except DBError as err:
                conn.rollback()
                flash(f'Database error: {str(err)}', 'danger')
                return render_template('register.html', form_data=form_data)
            
            except Exception as e:
                conn.rollback()
                flash(f'Registration error: {str(e)}', 'danger')
                return render_template('register.html', form_data=form_data)
            
            finally:
                if conn.is_connected():
                    conn.close()
        
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'danger')
            return render_template('register.html', 
                                 form_data=form_data if 'form_data' in locals() else None)
    
    return render_template('register.html', form_data=None)

# ======================
#  PATIENT ROUTES
# ======================

@app.route('/patient/dashboard')
@login_required(role='patient')
def patient_dashboard():
    user_id = session['user_id']

    patient = execute_query(
        "SELECT patient_id FROM Patients WHERE user_id = %s", (user_id,), fetch='one')

    if not patient:
        flash("Patient not found", "danger")
        return redirect(url_for('logout'))

    appointments = execute_query("""
        SELECT a.*, d.first_name AS doctor_first_name, d.last_name AS doctor_last_name,
               dep.name AS department_name
        FROM Appointments a
        JOIN Doctors d ON a.doctor_id = d.doctor_id
        JOIN Departments dep ON d.department_id = dep.department_id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (patient['patient_id'],), fetch='all')

    # Optional counts
    upcoming_count = sum(1 for appt in appointments if appt['status'] == 'Scheduled')
    completed_count = sum(1 for appt in appointments if appt['status'] == 'Completed')
    prescriptions_count = 0
    records_count = 0

    return render_template('patient_dashboard.html',
                           appointments=appointments,
                           upcoming_count=upcoming_count,
                           completed_count=completed_count,
                           prescriptions_count=prescriptions_count,
                           records_count=records_count)


from datetime import date, datetime, timedelta, time

@app.route('/appointments/book', methods=['GET', 'POST'])
@login_required(role='patient')
def book_appointment():
    departments = execute_query("SELECT department_id, name FROM Departments", fetch='all')
    selected_department = request.form.get('department')
    selected_doctor = request.form.get('doctor_id')
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    reason = request.form.get('reason', '')

    # Fetch only doctors from selected department
    doctors = []
    if selected_department:
        doctors = execute_query("""
            SELECT d.doctor_id, d.first_name, d.last_name, dep.name AS department_name, d.department_id
            FROM Doctors d
            JOIN Departments dep ON d.department_id = dep.department_id
            WHERE d.department_id = %s
            ORDER BY d.last_name
        """, (selected_department,), fetch='all')

    # Load doctor availability and time slots
    available_dates = []
    time_slots = []
    if selected_doctor:
        schedules = execute_query("""
            SELECT day_of_week, start_time, end_time
            FROM DoctorSchedules
            WHERE doctor_id = %s
        """, (selected_doctor,), fetch='all')

        today = date.today()
        for i in range(30):  # check next 30 days
            check_date = today + timedelta(days=i)
            weekday = check_date.strftime('%A')

            for schedule in schedules:
                if schedule['day_of_week'] == weekday:
                    available_dates.append(check_date.isoformat())

                    # Generate available time slots (30-minute intervals)
                    start_time = schedule['start_time']
                    end_time = schedule['end_time']
                    if isinstance(start_time, timedelta):
                        start_time = (datetime.min + start_time).time()
                    if isinstance(end_time, timedelta):
                        end_time = (datetime.min + end_time).time()

                    slot = datetime.combine(check_date, start_time)
                    end_slot = datetime.combine(check_date, end_time)
                    

                    while slot < end_slot:
                        time_slots.append(slot.strftime('%H:%M'))
                        slot += timedelta(minutes=30)

                    break  # matched this day, no need to check more

    # Handle booking submission
    if request.method == 'POST' and selected_doctor and date_str and time_str:
        # Check date is allowed
        if date_str not in available_dates:
            flash("❌ Selected date is not in the doctor's availability.", "danger")
            return redirect(url_for('book_appointment'))

        # Check time is allowed
        if time_str not in time_slots:
            flash("❌ Selected time is not in the doctor's schedule.", "danger")
            return redirect(url_for('book_appointment'))

        patient = execute_query("SELECT patient_id FROM Patients WHERE user_id = %s", (session['user_id'],), fetch='one')
        if not patient:
            flash("❌ Patient record not found.", "danger")
            return redirect(url_for('patient_dashboard'))

        # Save appointment
        success = execute_query("""
            INSERT INTO Appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status)
            VALUES (%s, %s, %s, %s, %s, 'Scheduled')
        """, (patient['patient_id'], selected_doctor, date_str, time_str, reason))

        if success:
            flash("✅ Appointment booked!", "success")
            return redirect(url_for('patient_dashboard'))
        else:
            flash("❌ Failed to book appointment.", "danger")

    current_date = date.today().isoformat()
    return render_template(
        "book_appointment.html",
        departments=departments,
        doctors=doctors,
        selected_department=selected_department,
        selected_doctor=selected_doctor,
        available_dates=available_dates,
        time_slots=time_slots,
        current_date=current_date
    )


@app.route('/appointments/<int:appointment_id>/view')
@login_required(role='patient')
def view_appointment(appointment_id):
    appointment = execute_query("""
        SELECT a.*, d.first_name AS doctor_first_name, d.last_name AS doctor_last_name,
               dep.name AS department_name
        FROM Appointments a
        JOIN Doctors d ON a.doctor_id = d.doctor_id
        JOIN Departments dep ON d.department_id = dep.department_id
        WHERE a.appointment_id = %s
    """, (appointment_id,), fetch='one')

    if not appointment:
        flash('❌ Appointment not found', 'danger')
        return redirect(url_for('patient_dashboard'))

    return render_template('view_appointment.html', appointment=appointment)

@app.route('/get_doctors/<int:department_id>')
@login_required(role='patient')
def get_doctors_by_department(department_id):
    doctors = execute_query("""
        SELECT doctor_id, first_name, last_name 
        FROM Doctors 
        WHERE department_id = %s
        ORDER BY last_name
    """, (department_id,), fetch='all')

    return jsonify(doctors)

@app.route('/appointments/<int:appointment_id>/cancel', methods=['GET'])
@login_required(role='patient')
def cancel_patient_appointment(appointment_id):
    appointment = execute_query("""
        SELECT a.*, p.user_id
        FROM Appointments a
        JOIN Patients p ON a.patient_id = p.patient_id
        WHERE a.appointment_id = %s
    """, (appointment_id,), fetch='one')

    if not appointment:
        flash('❌ Appointment not found.', 'danger')
        return redirect(url_for('patient_dashboard'))

    if appointment['user_id'] != session['user_id']:
        flash("❌ You don't have permission to cancel this appointment.", "danger")
        return redirect(url_for('patient_dashboard'))

    success = execute_query(
        "UPDATE Appointments SET status = 'Cancelled' WHERE appointment_id = %s",
        (appointment_id,)
    )

    if success:
        flash("✅ Appointment cancelled successfully.", "success")
    else:
        flash("❌ Failed to cancel appointment.", "danger")

    return redirect(url_for('patient_dashboard'))



# ======================
#  DOCTOR ROUTES
# ======================

@app.route('/doctor/dashboard')
@login_required(role='doctor')
def doctor_dashboard():
    """Doctor dashboard with appointments"""
    doctor = execute_query(
        """SELECT d.*, dep.name AS department_name 
           FROM Doctors d
           JOIN Departments dep ON d.department_id = dep.department_id
           WHERE d.user_id = %s""",
        (session['user_id'],),
        fetch='one'
    )
    
    if not doctor:
        flash('Doctor record not found', 'danger')
        return redirect(url_for('logout'))
    
    appointments = execute_query(
        """SELECT a.*, p.first_name AS patient_first_name, p.last_name AS patient_last_name,
                  p.phone_number AS patient_phone
           FROM Appointments a
           JOIN Patients p ON a.patient_id = p.patient_id
           WHERE a.doctor_id = %s AND a.status = 'Scheduled'
           ORDER BY a.appointment_date, a.appointment_time""",
        (doctor['doctor_id'],),
        fetch='all'
    )
    
    return render_template('doctor_dashboard.html', 
                         doctor=doctor, 
                         appointments=appointments or [])

# ======================
#  ADMIN ROUTES
# ======================

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    print("✅ Entered admin_dashboard route")

    try:
        stats = {
            'patients': execute_query("SELECT COUNT(*) AS count FROM Patients", fetch='one')['count'] or 0,
            'doctors': execute_query("SELECT COUNT(*) AS count FROM Doctors", fetch='one')['count'] or 0,
            'appointments': execute_query("SELECT COUNT(*) AS count FROM Appointments", fetch='one')['count'] or 0,
            'pending': execute_query("SELECT COUNT(*) AS count FROM Appointments WHERE status='Scheduled'", fetch='one')['count'] or 0
        }

        appointments = execute_query(
            """SELECT a.*, p.first_name AS patient_first, p.last_name AS patient_last,
                      d.first_name AS doctor_first, d.last_name AS doctor_last,
                      dep.name AS department
               FROM Appointments a
               JOIN Patients p ON a.patient_id = p.patient_id
               JOIN Doctors d ON a.doctor_id = d.doctor_id
               JOIN Departments dep ON d.department_id = dep.department_id
               ORDER BY a.appointment_date DESC, a.appointment_time DESC
               LIMIT 100""",
            fetch='all'
        )

        doctors = execute_query(
            "SELECT doctor_id, first_name, last_name FROM Doctors ORDER BY last_name LIMIT 5",
            fetch='all'
        )

        print("📊 Admin stats loaded")

        return render_template('admin_dashboard.html',
                               stats=stats,
                               appointments=appointments or [],
                               doctors=doctors or [])
    except Exception as e:
        print("❌ Error in admin_dashboard:", e)
        flash("Failed to load admin dashboard", "danger")
        return redirect(url_for('home'))

@app.route('/admin/doctors')
@login_required(role='admin')
def admin_doctors():
    """View and manage all doctors"""
    doctors = execute_query(
        """SELECT d.*, dep.name AS department_name, u.email 
           FROM Doctors d
           JOIN Departments dep ON d.department_id = dep.department_id
           JOIN Users u ON d.user_id = u.user_id
           ORDER BY d.last_name""",
        fetch='all'
    )
    
    departments = execute_query(
        "SELECT * FROM Departments ORDER BY name",
        fetch='all'
    )
    
    return render_template('admin_doctors.html',
                         doctors=doctors or [],
                         departments=departments or [])

@app.route('/admin/doctor/add', methods=['GET', 'POST'])
@login_required(role='admin')
def add_doctor():
    """Add a new doctor with comprehensive error handling"""
    if request.method == 'POST':
        try:
            # Get and validate form data
            form_data = {
                'username': request.form.get('username', '').strip(),
                'email': request.form.get('email', '').strip().lower(),
                'password': request.form.get('password', '').strip(),
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'department_id': request.form.get('department_id'),
                'specialization': request.form.get('specialization', '').strip(),
                'license_number': request.form.get('license_number', '').strip(),
                'years_exp': request.form.get('years_experience', '0'),
                'phone': request.form.get('phone', '').strip(),
                'bio': request.form.get('bio', '').strip()
            }

            # Validate required fields
            required_fields = ['username', 'email', 'password', 'first_name', 
                             'last_name', 'department_id', 'specialization', 'license_number']
            for field in required_fields:
                if not form_data[field]:
                    flash(f'{field.replace("_", " ").title()} is required', 'danger')
                    return redirect(url_for('add_doctor'))

            if len(form_data['password']) < 8:
                flash('Password must be at least 8 characters', 'danger')
                return redirect(url_for('add_doctor'))

            # Check for existing user
            existing_user = execute_query(
                "SELECT user_id FROM Users WHERE username = %s OR email = %s",
                (form_data['username'], form_data['email']),
                fetch='one'
            )
            if existing_user:
                flash('Username or email already exists', 'danger')
                return redirect(url_for('add_doctor'))

            # Check department exists
            department = execute_query(
                "SELECT department_id FROM Departments WHERE department_id = %s",
                (form_data['department_id'],),
                fetch='one'
            )
            if not department:
                flash('Selected department does not exist', 'danger')
                return redirect(url_for('add_doctor'))

            # Create user account
            hashed_pw = generate_password_hash(form_data['password'])
            user_id = execute_query(
                """INSERT INTO Users (username, password_hash, email, user_type)
                   VALUES (%s, %s, %s, 'doctor')""",
                (form_data['username'], hashed_pw, form_data['email']),
                lastrow=True
            )
            if not user_id:
                flash('Failed to create user account', 'danger')
                return redirect(url_for('add_doctor'))

            # Create doctor record
            doctor_success = execute_query(
                """INSERT INTO Doctors 
                   (user_id, department_id, first_name, last_name, specialization, 
                    license_number, years_of_experience, phone_number, biography)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, form_data['department_id'], form_data['first_name'], 
                 form_data['last_name'], form_data['specialization'],
                 form_data['license_number'], int(form_data['years_exp']),
                 form_data['phone'], form_data['bio'])
            )

            if doctor_success:
                flash('Doctor added successfully!', 'success')
                return redirect(url_for('admin_doctors'))
            
            flash('Failed to create doctor profile', 'danger')
        
        except Exception as e:
            print(f"Error adding doctor: {str(e)}")
            flash('An error occurred while adding the doctor', 'danger')

    # GET request or failed POST - show form
    departments = execute_query("SELECT * FROM Departments", fetch='all')
    return render_template('add_doctor.html', 
                         departments=departments or [],
                         form_data=form_data if request.method == 'POST' else None)

@app.route('/admin/doctor/<int:doctor_id>/delete', methods=['POST'])
@login_required(role='admin')
def delete_doctor(doctor_id):
    """Delete a doctor record"""
    # First get user_id to delete from Users table
    doctor = execute_query(
        "SELECT user_id FROM Doctors WHERE doctor_id = %s",
        (doctor_id,),
        fetch='one'
    )
    
    if doctor:
        # Delete from Doctors first to maintain referential integrity
        execute_query(
            "DELETE FROM Doctors WHERE doctor_id = %s",
            (doctor_id,)
        )
        
        # Then delete from Users
        execute_query(
            "DELETE FROM Users WHERE user_id = %s",
            (doctor['user_id'],)
        )
        
        flash('Doctor deleted successfully', 'success')
    else:
        flash('Doctor not found', 'danger')
    
    return redirect(url_for('admin_doctors'))

@app.route('/admin/appointment/<int:appointment_id>/update', methods=['POST'])
@login_required(role='admin')
def update_appointment(appointment_id):
    """Update appointment details"""
    if request.method == 'POST':
        success = execute_query(
            """UPDATE Appointments
               SET appointment_date = %s,
                   appointment_time = %s,
                   status = %s,
                   doctor_id = %s,
                   notes = %s
               WHERE appointment_id = %s""",
            (request.form['date'], request.form['time'], request.form['status'],
             request.form['doctor_id'], request.form.get('notes', ''), appointment_id)
        )
        
        if success:
            flash('Appointment updated successfully', 'success')
        else:
            flash('Failed to update appointment', 'danger')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required(role='admin')
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    success = execute_query(
        "UPDATE Appointments SET status = 'Cancelled' WHERE appointment_id = %s",
        (appointment_id,)
    )
    
    if success:
        flash('Appointment cancelled successfully', 'success')
    else:
        flash('Failed to cancel appointment', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_department', methods=['POST'])
@login_required(role='admin')
def add_department():
    """Add a new department via AJAX"""
    try:
        name = request.form.get('name')
        description = request.form.get('description', '')
        location = request.form.get('location', '')
        
        if not name:
            return jsonify({'success': False, 'message': 'Department name is required'})
        
        # Check if department already exists
        existing = execute_query(
            "SELECT department_id FROM Departments WHERE name = %s",
            (name,),
            fetch='one'
        )
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Department already exists',
                'department_id': existing['department_id']
            })
        
        # Insert new department
        department_id = execute_query(
            "INSERT INTO Departments (name, description, location) VALUES (%s, %s, %s)",
            (name, description, location),
            lastrow=True
        )
        
        if department_id:
            return jsonify({
                'success': True,
                'department_id': department_id,
                'name': name
            })
        return jsonify({'success': False, 'message': 'Database error'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
# ======================
#  INITIALIZATION
# ======================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)