from flask import Flask, request, render_template, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session

# Database config
db_config = {
    'host': 'localhost',
    'user': 'root',         # <-- Replace
    'password': '1234', # <-- Replace
    'database': 'signin_db'
}

# Home (Login page)
@app.route('/')
def home():
    return render_template('login.html')

# Sign In page (new user)
@app.route('/signin-page')
def signin_page():
    return render_template('signin.html')

# Handle sign in (create user)
@app.route('/signin', methods=['POST'])
def signin():
    username = request.form['username']
    password = request.form['password']
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return redirect(url_for('home'))
    except mysql.connector.IntegrityError:
        return "<h3>Username already exists.</h3>"
    except Exception as e:
        return f"<h3>Error: {e}</h3>"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# Handle login validation
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session['username'] = username
            return redirect(url_for('welcome'))
        else:
            return render_template('login.html', error="Invalid username or password")
    except Exception as e:
        return f"<h3>Login Error: {e}</h3>"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Welcome page after successful login
@app.route('/welcome')
def welcome():
    if 'username' in session:
        return render_template('welcome.html', username=session['username'])
    else:
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)