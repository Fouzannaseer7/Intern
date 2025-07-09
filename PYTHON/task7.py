import mysql.connector
from tabulate import tabulate

# Database connection configuration
config = {
    'user': 'root',
    'password': 'Founas@123',
    'host': 'localhost',
    'database': 'student_management'
}

try:
    # Connect to MySQL server (without specifying a database first)
    conn = mysql.connector.connect(
        user=config['user'],
        password=config['password'],
        host=config['host']
    )
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
    conn.close()
    
    # Now connect to the specific database
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Create the student_marks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_marks (
        student_id INT AUTO_INCREMENT PRIMARY KEY,
        student_name VARCHAR(100) NOT NULL,
        subject1_name VARCHAR(50),
        subject1_mark DECIMAL(5,2),
        subject2_name VARCHAR(50),
        subject2_mark DECIMAL(5,2),
        subject3_name VARCHAR(50),
        subject3_mark DECIMAL(5,2),
        subject4_name VARCHAR(50),
        subject4_mark DECIMAL(5,2),
        subject5_name VARCHAR(50),
        subject5_mark DECIMAL(5,2),
        cgpa DECIMAL(3,2)
    )
    ''')
    
    # Insert sample data
    sample_data = [
        ('John Doe', 'Mathematics', 85.0, 'Physics', 78.0, 'Chemistry', 82.0, 'Biology', 90.0, 'English', 88.0, 3.70),
        ('Jane Smith', 'Mathematics', 92.0, 'Physics', 88.0, 'Chemistry', 85.0, 'Biology', 94.0, 'English', 90.0, 3.90),
        ('Bob Johnson', 'Mathematics', 75.0, 'Physics', 72.0, 'Chemistry', 68.0, 'Biology', 80.0, 'English', 78.0, 3.20),
        ('Alice Williams', 'Mathematics', 88.0, 'Physics', 85.0, 'Chemistry', 90.0, 'Biology', 92.0, 'English', 87.0, 3.80),
        ('Charlie Brown', 'Mathematics', 65.0, 'Physics', 60.0, 'Chemistry', 58.0, 'Biology', 70.0, 'English', 68.0, 2.80)
    ]
    
    insert_query = '''
    INSERT INTO student_marks 
    (student_name, subject1_name, subject1_mark, subject2_name, subject2_mark, 
     subject3_name, subject3_mark, subject4_name, subject4_mark, 
     subject5_name, subject5_mark, cgpa)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    
    cursor.executemany(insert_query, sample_data)
    conn.commit()
    
    # Fetch and display the data
    cursor.execute('SELECT * FROM student_marks')
    rows = cursor.fetchall()
    
    # Prepare headers
    headers = ["ID", "Student Name", "Subject 1", "Mark 1", "Subject 2", "Mark 2", 
               "Subject 3", "Mark 3", "Subject 4", "Mark 4", "Subject 5", "Mark 5", "CGPA"]
    
    # Display using tabulate
    print("\nStudent Marks and CGPA Records:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    
except mysql.connector.Error as err:
    print(f"Error: {err}")
    
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("\nMySQL connection is closed")