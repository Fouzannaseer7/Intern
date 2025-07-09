import mysql.connector
from mysql.connector import Error
from tabulate import tabulate

def create_connection():
    """Create a database connection to the existing MySQL database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Founas@123',
            database='student_man'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def calculate_cgpa(marks_list):
    """Calculate CGPA based on marks (10-point scale)"""
    total = sum(marks_list)
    percentage = (total / (len(marks_list) * 100)) * 100
    cgpa = min(10.0, percentage / 9.5)  # Cap at 10.0
    return round(cgpa, 2)

def validate_mark(mark):
    """Validate that mark is between 0-100"""
    try:
        mark = float(mark)
        if 0 <= mark <= 100:
            return mark
        else:
            print("Error: Marks must be between 0 and 100")
            return None
    except ValueError:
        print("Invalid input. Please enter a numeric value.")
        return None

def check_pass_status(marks):
    """Determine pass/fail status and which subjects were failed"""
    failed_subjects = []
    subjects = ['Maths', 'Physics', 'Chemistry', 'Biology', 'English']
    
    for i, mark in enumerate(marks):
        if mark < 45:
            failed_subjects.append(subjects[i])
    
    if failed_subjects:
        return ('Failed', failed_subjects)
    return ('Passed', [])

def verify_table_structure(connection):
    """Verify the students table has all required columns"""
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'student_man' 
            AND TABLE_NAME = 'students'
        """)
        
        existing_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        required_columns = {
            'student_id', 'student_name', 
            'subject1', 'marks1', 'subject2', 'marks2',
            'subject3', 'marks3', 'subject4', 'marks4',
            'subject5', 'marks5', 'total_marks', 'cgpa',
            'pass_fail_status'
        }
        
        missing_columns = required_columns - existing_columns
        if missing_columns:
            print(f"Missing columns in database: {missing_columns}")
            return False
        
        return True
    except Error as e:
        print(f"Error verifying table structure: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def add_student(connection):
    """Add a new student with validated marks and pass/fail status"""
    print("\nEnter Student Details:")
    
    student_data = {'name': input("Student Name: ")}
    subjects = ['Maths', 'Physics', 'Chemistry', 'Biology', 'English']
    
    for i, subject in enumerate(subjects):
        while True:
            mark = validate_mark(input(f"{subject} Marks (0-100): "))
            if mark is not None:
                student_data[f'marks{i+1}'] = mark
                break
    
    # Calculate total, CGPA and pass/fail status
    marks = [student_data[f'marks{i}'] for i in range(1, 6)]
    total = sum(marks)
    cgpa = calculate_cgpa(marks)
    status, failed_subjects = check_pass_status(marks)
    
    cursor = None
    try:
        cursor = connection.cursor()
        query = """INSERT INTO students 
                  (student_name, subject1, marks1, subject2, marks2, 
                   subject3, marks3, subject4, marks4, subject5, marks5, 
                   total_marks, cgpa, pass_fail_status)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (
            student_data['name'],
            'Maths', student_data['marks1'],
            'Physics', student_data['marks2'],
            'Chemistry', student_data['marks3'],
            'Biology', student_data['marks4'],
            'English', student_data['marks5'],
            total, cgpa, status
        ))
        connection.commit()
        print(f"\nStudent {student_data['name']} added successfully!")
        print(f"Total Marks: {total}, CGPA: {cgpa}")
        if status == 'Failed':
            print(f"Status: Failed in {', '.join(failed_subjects)}")
        else:
            print("Status: Passed in all subjects")
    except Error as e:
        print(f"Error adding student: {e}")
        connection.rollback()
    finally:
        if cursor:
            cursor.close()

def view_students(connection):
    """View all students in a formatted table with pass/fail status"""
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT student_id, student_name, 
                   marks1, marks2, marks3, marks4, marks5,
                   total_marks, cgpa, pass_fail_status
            FROM students
            ORDER BY student_id
        """)
        
        students = cursor.fetchall()
        
        if not students:
            print("\nNo students found in database.")
            return
        
        table = []
        for student in students:
            marks = [float(student[f'marks{i}']) for i in range(1, 6)]
            status, failed_subjects = check_pass_status(marks)
            status_display = status
            if failed_subjects:
                status_display += f" in {', '.join(failed_subjects)}"
            
            table.append([
                student['student_id'],
                student['student_name'],
                float(student['marks1']),
                float(student['marks2']),
                float(student['marks3']),
                float(student['marks4']),
                float(student['marks5']),
                float(student['total_marks']),
                float(student['cgpa']),
                status_display
            ])
        
        print("\nStudent Records:")
        print(tabulate(table, 
                     headers=["ID", "Name", "Maths", "Physics", 
                             "Chemistry", "Biology", "English", 
                             "Total", "CGPA", "Status"],
                     tablefmt="grid"))
    except Error as e:
        print(f"Error retrieving students: {e}")
    finally:
        if cursor:
            cursor.close()

def edit_student_marks(connection):
    """Edit marks for an existing student with validation and update pass/fail status"""
    view_students(connection)
    
    try:
        student_id = int(input("\nEnter the ID of the student to edit: "))
    except ValueError:
        print("Invalid input. Please enter a numeric ID.")
        return
    
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT marks1, marks2, marks3, marks4, marks5
            FROM students
            WHERE student_id = %s
        """, (student_id,))
        
        student = cursor.fetchone()
        if not student:
            print(f"No student found with ID {student_id}")
            return
        
        subjects = ['Maths', 'Physics', 'Chemistry', 'Biology', 'English']
        print("\nCurrent marks:")
        for i, subject in enumerate(subjects):
            print(f"{i+1}. {subject}: {float(student[f'marks{i+1}'])}")
        
        # Get which mark to edit
        while True:
            try:
                mark_num = int(input("\nEnter the number of the mark to edit (1-5): "))
                if mark_num < 1 or mark_num > 5:
                    print("Please enter a number between 1 and 5")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        # Get new mark with validation
        while True:
            new_mark = validate_mark(input(f"Enter new mark for {subjects[mark_num-1]} (0-100): "))
            if new_mark is not None:
                break
        
        # Update marks and calculations
        marks = [float(student[f'marks{i}']) if i != mark_num else new_mark for i in range(1, 6)]
        total = sum(marks)
        cgpa = calculate_cgpa(marks)
        status, failed_subjects = check_pass_status(marks)
        
        cursor.execute(f"""
            UPDATE students 
            SET marks{mark_num} = %s, 
                total_marks = %s, 
                cgpa = %s, 
                pass_fail_status = %s
            WHERE student_id = %s
        """, (new_mark, total, cgpa, status, student_id))
        
        connection.commit()
        print(f"\nMark updated successfully!")
        print(f"New total marks: {total}, New CGPA: {cgpa}")
        if status == 'Failed':
            print(f"Status: Failed in {', '.join(failed_subjects)}")
        else:
            print("Status: Passed in all subjects")
        
    except Error as e:
        print(f"Error updating student marks: {e}")
        connection.rollback()
    finally:
        if cursor:
            cursor.close()

def main_menu():
    """Display the main menu options"""
    print("\nStudent Management System")
    print("1. Add New Student")
    print("2. View All Students")
    print("3. Edit Student Marks")
    print("4. Exit")
    while True:
        choice = input("Enter your choice (1-4): ")
        if choice in ('1', '2', '3', '4'):
            return choice
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

def main():
    connection = create_connection()
    if not connection:
        return
    
    try:
        # Verify table structure before proceeding
        if not verify_table_structure(connection):
            print("\nPlease ensure your database table has all required columns:")
            print("1. Run this SQL command to add the missing column:")
            print("   ALTER TABLE students ADD COLUMN pass_fail_status VARCHAR(10) DEFAULT 'Failed';")
            print("2. Make sure all other required columns exist")
            return
        
        while True:
            choice = main_menu()
            
            if choice == '1':
                add_student(connection)
            elif choice == '2':
                view_students(connection)
            elif choice == '3':
                edit_student_marks(connection)
            elif choice == '4':
                print("\nExiting program...")
                break
                
    except Error as e:
        print(f"\nDatabase error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
