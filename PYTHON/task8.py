import mysql.connector
from mysql.connector import Error

def create_connection():
    """Create a database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Replace with your MySQL username
            password='Founas@123',  # Replace with your MySQL password
            database='student_managements'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def view_records():
    """View records from the database"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            print("\n1. View Students")
            print("2. View Subjects")
            print("3. View Marks")
            print("4. View All Records")
            choice = input("Enter your choice (1-4): ")
            
            if choice == '1':
                cursor.execute("SELECT * FROM students")
                records = cursor.fetchall()
                print("\nStudents:")
                for row in records:
                    print(f"ID: {row['student_id']}, Name: {row['student_name']}, CGPA: {row['total_cgpa']}")
                    
            elif choice == '2':
                cursor.execute("SELECT * FROM subjects")
                records = cursor.fetchall()
                print("\nSubjects:")
                for row in records:
                    print(f"ID: {row['subject_id']}, Name: {row['subject_name']}")
                    
            elif choice == '3':
                cursor.execute("""
                    SELECT sm.mark_id, s.student_name, sub.subject_name, sm.mark 
                    FROM student_marks sm
                    JOIN students s ON sm.student_id = s.student_id
                    JOIN subjects sub ON sm.subject_id = sub.subject_id
                """)
                records = cursor.fetchall()
                print("\nStudent Marks:")
                for row in records:
                    print(f"Mark ID: {row['mark_id']}, Student: {row['student_name']}, Subject: {row['subject_name']}, Mark: {row['mark']}")
                    
            elif choice == '4':
                # View all records
                print("\nStudents:")
                cursor.execute("SELECT * FROM students")
                for row in cursor.fetchall():
                    print(f"ID: {row['student_id']}, Name: {row['student_name']}, CGPA: {row['total_cgpa']}")
                
                print("\nSubjects:")
                cursor.execute("SELECT * FROM subjects")
                for row in cursor.fetchall():
                    print(f"ID: {row['subject_id']}, Name: {row['subject_name']}")
                
                print("\nMarks:")
                cursor.execute("""
                    SELECT sm.mark_id, s.student_name, sub.subject_name, sm.mark 
                    FROM student_marks sm
                    JOIN students s ON sm.student_id = s.student_id
                    JOIN subjects sub ON sm.subject_id = sub.subject_id
                """)
                for row in cursor.fetchall():
                    print(f"Mark ID: {row['mark_id']}, Student: {row['student_name']}, Subject: {row['subject_name']}, Mark: {row['mark']}")
                    
            else:
                print("Invalid choice!")
                
        except Error as e:
            print(f"Error viewing records: {e}")
        finally:
            cursor.close()
            connection.close()

def insert_record():
    """Insert a new record into the database"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            print("\n1. Insert Student")
            print("2. Insert Subject")
            print("3. Insert Mark")
            choice = input("Enter your choice (1-3): ")
            
            if choice == '1':
                name = input("Enter student name: ")
                cursor.execute("INSERT INTO students (student_name) VALUES (%s)", (name,))
                connection.commit()
                print("Student added successfully!")
                
            elif choice == '2':
                name = input("Enter subject name: ")
                cursor.execute("INSERT INTO subjects (subject_name) VALUES (%s)", (name,))
                connection.commit()
                print("Subject added successfully!")
                
            elif choice == '3':
                student_id = input("Enter student ID: ")
                subject_id = input("Enter subject ID: ")
                mark = input("Enter mark: ")
                cursor.execute("""
                    INSERT INTO student_marks (student_id, subject_id, mark) 
                    VALUES (%s, %s, %s)
                """, (student_id, subject_id, mark))
                connection.commit()
                
                # Update CGPA after adding marks
                cursor.callproc('calculate_cgpa')
                connection.commit()
                print("Mark added and CGPA updated successfully!")
                
            else:
                print("Invalid choice!")
                
        except Error as e:
            print(f"Error inserting record: {e}")
        finally:
            cursor.close()
            connection.close()

def delete_record():
    """Delete a record from the database"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            print("\n1. Delete Student")
            print("2. Delete Subject")
            print("3. Delete Mark")
            choice = input("Enter your choice (1-3): ")
            
            if choice == '1':
                student_id = input("Enter student ID to delete: ")
                # First delete marks for this student
                cursor.execute("DELETE FROM student_marks WHERE student_id = %s", (student_id,))
                # Then delete the student
                cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
                connection.commit()
                print("Student and associated marks deleted successfully!")
                
            elif choice == '2':
                subject_id = input("Enter subject ID to delete: ")
                # First check if there are marks for this subject
                cursor.execute("SELECT COUNT(*) FROM student_marks WHERE subject_id = %s", (subject_id,))
                count = cursor.fetchone()[0]
                if count > 0:
                    confirm = input(f"Warning: {count} marks are associated with this subject. Delete anyway? (y/n): ")
                    if confirm.lower() != 'y':
                        print("Deletion cancelled.")
                        return
                cursor.execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
                connection.commit()
                print("Subject deleted successfully!")
                
            elif choice == '3':
                mark_id = input("Enter mark ID to delete: ")
                cursor.execute("DELETE FROM student_marks WHERE mark_id = %s", (mark_id,))
                connection.commit()
                
                # Update CGPA after deleting mark
                cursor.callproc('calculate_cgpa')
                connection.commit()
                print("Mark deleted and CGPA updated successfully!")
                
            else:
                print("Invalid choice!")
                
        except Error as e:
            print(f"Error deleting record: {e}")
        finally:
            cursor.close()
            connection.close()

def main():
    """Main menu function"""
    while True:
        print("\nStudent Management System")
        print("1. View Records")
        print("2. Insert Record")
        print("3. Delete Record")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == '1':
            view_records()
        elif choice == '2':
            insert_record()
        elif choice == '3':
            delete_record()
        elif choice == '4':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()