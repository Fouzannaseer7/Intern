from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration - update with your credentials
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Founas@123',
    'database': 'hospital_db'
}

def get_db_connection():
    """Establish connection to MySQL database"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        flash(f"Database connection error: {e}", 'danger')
        return None

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('appointments'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, full_name FROM users WHERE username = %s AND password = %s", 
                    (username, password)
                )
                user = cursor.fetchone()
                
                if user:
                    session['user_id'] = user['id']
                    session['full_name'] = user['full_name']
                    flash('Login successful!', 'success')
                    return redirect(url_for('appointments'))
                else:
                    flash('Invalid username or password', 'danger')
            except Error as e:
                flash(f"Database error: {e}", 'danger')
            finally:
                conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Check if username exists
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('Username already exists', 'danger')
                    return redirect(url_for('register'))
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (full_name, email, username, password) VALUES (%s, %s, %s, %s)",
                    (fullname, email, username, password)
                )
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                flash(f"Database error: {e}", 'danger')
            finally:
                conn.close()
    
    return render_template('register.html')

@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    if 'user_id' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Check if all required fields are present
        required_fields = ['doctor', 'date', 'time', 'reason']
        if not all(field in request.form for field in required_fields):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('appointments'))
        
        try:
            doctor = request.form['doctor']
            date_str = request.form['date']
            time_str = request.form['time']
            reason = request.form['reason']
            
            # Validate date and time
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time_str, "%H:%M").time()
            
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT INTO appointments 
                        (user_id, doctor_name, appointment_date, appointment_time, reason)
                        VALUES (%s, %s, %s, %s, %s)""",
                        (session['user_id'], doctor, appointment_date, appointment_time, reason)
                    )
                    conn.commit()
                    flash('Appointment scheduled successfully!', 'success')
                except Error as e:
                    flash(f"Database error: {e}", 'danger')
                finally:
                    conn.close()
        except ValueError:
            flash('Invalid date or time format. Use YYYY-MM-DD and HH:MM', 'danger')
            return redirect(url_for('appointments'))
        except KeyError as e:
            flash(f'Missing required field: {e}', 'danger')
            return redirect(url_for('appointments'))
    
    return render_template('appointments.html', full_name=session['full_name'])

@app.route('/view')
def view_appointments():
    if 'user_id' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    appointments = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT doctor_name, appointment_date, appointment_time, reason 
                FROM appointments 
                WHERE user_id = %s 
                ORDER BY appointment_date, appointment_time""",
                (session['user_id'],)
            )
            appointments = cursor.fetchall()
        except Error as e:
            flash(f"Database error: {e}", 'danger')
        finally:
            conn.close()
    
    return render_template('view.html', appointments=appointments)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)