import mysql.connector
from tabulate import tabulate

def connect_to_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",  # replace with your MySQL username
            password="Founas@123",   # replace with your MySQL password
            database="student_managements"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def display_student_records():
    conn = connect_to_database()
    if not conn:
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all students
        cursor.execute("SELECT * FROM students ORDER BY student_id")
        students = cursor.fetchall()
        
        # For each student, get their marks and subjects
        for student in students:
            print(f"\nStudent ID: {student['student_id']}")
            print(f"Name: {student['student_name']}")
            print(f"CGPA: {student['total_cgpa']:.2f}")
            
            # Get marks for this student
            cursor.execute("""
                SELECT s.subject_name, sm.mark 
                FROM student_marks sm
                JOIN subjects s ON sm.subject_id = s.subject_id
                WHERE sm.student_id = %s
            """, (student['student_id'],))
            
            marks = cursor.fetchall()
            
            # Display marks in a table
            print("\nSubject Marks:")
            print(tabulate(marks, headers="keys", tablefmt="grid"))
            
            # Calculate and display percentage
            total_marks = sum(mark['mark'] for mark in marks)
            percentage = total_marks / len(marks)
            print(f"\nAverage Percentage: {percentage:.2f}%")
            
            print("\n" + "="*50)
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def display_all_students_summary():
    conn = connect_to_database()
    if not conn:
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all students with their CGPA
        cursor.execute("""
            SELECT s.student_id, s.student_name, s.total_cgpa, 
                   AVG(sm.mark) as avg_percentage
            FROM students s
            JOIN student_marks sm ON s.student_id = sm.student_id
            GROUP BY s.student_id, s.student_name, s.total_cgpa
            ORDER BY s.total_cgpa DESC
        """)
        
        students = cursor.fetchall()
        
        # Display summary table
        print("\nAll Students Summary (Ordered by CGPA):")
        print(tabulate(students, headers="keys", tablefmt="grid"))
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Student Academic Records System\n")
    
    while True:
        print("\nMenu:")
        print("1. Display detailed records for all students")
        print("2. Display summary of all students")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            display_student_records()
        elif choice == "2":
            display_all_students_summary()
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please try again.")