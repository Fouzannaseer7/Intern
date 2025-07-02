import mysql.connector
from mysql.connector import Error

def main():
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(
            host='localhost',        # Replace with your host
            user='root',    # Replace with your username
            password='Founas@123', # Replace with your password
            database='sdlc_d'  # Replace with your database name
        )

        if conn.is_connected():
            print("Successfully connected to the database.")
        else:
            print("Failed to connect to the database.")
            return

        cursor = conn.cursor()

        # Create a table (if it doesn't exist)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_phases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phase VARCHAR(255),
            detail1 VARCHAR(255),
            detail2 VARCHAR(255),
            detail3 VARCHAR(255),
            detail4 VARCHAR(255)
        )
        ''')

        # Data to be displayed
        data = {
            'Planning': ['Planning', 'Define Project Scope', 'Set objectives and goals', 'Resource planning', ''],
            'Defining Requirements': ['Defining', 'Functional requirements', 'Technical requirements', 'Requirements reviewed and approved', ''],
            'Designing': ['Design', 'Low-level Design', 'High-level Design', '', ''],
            'Development': ['Development', 'Coding standard', 'Scalable coding', 'Version control', 'Code review'],
            'Testing': ['Unit testing', 'Manual Testing', 'Automated Testing', '', ''],
            'Deployment and Maintenance': ['Deployment and Maintenance', 'Release planning', 'Deployment Automation', 'Maintenance', 'Feedback']
        }

        phases = list(data.keys())

        while True:
            print("\nAvailable phases:")
            for idx, phase in enumerate(phases, start=1):
                print(f"{idx}. {phase}")

            user_input = input("\nEnter the phase number to view details (or type 'exit'/'quit' to stop): ").strip().lower()

            if user_input in ('exit', 'quit'):
                print("Exiting program.")
                break

            if not user_input.isdigit():
                print("Invalid input. Please enter a number or 'exit'/'quit'.")
                continue

            index = int(user_input) - 1
            if 0 <= index < len(phases):
                selected_phase = phases[index]
                print(f"\nDetails for phase '{selected_phase}':")
                details = data[selected_phase]
                for i, detail in enumerate(details, start=1):
                    if detail:
                        print(f"{i}. {detail}")
            else:
                print("Number out of range. Please enter a valid phase number.")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
