import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Founas@123',
    'database': 'sdlc_d'
}

# SDLC phases mapping
SDLC_PHASES = {
    1: "Planning",
    2: "Defining Requirements",
    3: "Designing",
    4: "Development",
    5: "Testing",
    6: "Deployment and Maintenance"
}

def connect_db(use_database=True):
    """Establish database connection"""
    config = DB_CONFIG.copy()
    if not use_database:
        config.pop('database', None)
    
    try:
        return mysql.connector.connect(**config)
    except Error as e:
        print(f"\nDatabase connection error: {e}")
        return None

def initialize_db():
    """Initialize database and table"""
    print("\nInitializing database...")
    db = connect_db(use_database=False)
    if not db:
        return False
    
    cursor = db.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sdlc_5(
            id INT AUTO_INCREMENT PRIMARY KEY,
            phase_name VARCHAR(50) NOT NULL,
            attribute1 VARCHAR(100),
            attribute2 VARCHAR(100),
            attribute3 VARCHAR(100),
            attribute4 VARCHAR(100)
        )
        """)
        db.commit()
        return True
    except Error as e:
        print(f"Initialization error: {e}")
        return False
    finally:
        cursor.close()
        db.close()

def insert_record():
    """Insert new SDLC phase record"""
    db = connect_db()
    if not db:
        return
    
    cursor = db.cursor()
    try:
        print("\nAvailable Phases:")
        for num, phase in SDLC_PHASES.items():
            print(f"{num}. {phase}")
        
        phase_num = int(input("\nEnter Phase Number: "))
        phase_name = SDLC_PHASES.get(phase_num)
        if not phase_name:
            print("Invalid phase number!")
            return
        
        print(f"\nEntering data for: {phase_name}")
        attrs = [input(f"Attribute {i+1}: ") for i in range(4)]
        
        cursor.execute("""
        INSERT INTO sdlc_5 (phase_name, attribute1, attribute2, attribute3, attribute4)
        VALUES (%s, %s, %s, %s, %s)
        """, (phase_name, *attrs))
        db.commit()
        print("Record inserted successfully!")
    except ValueError:
        print("Please enter valid numbers!")
    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        db.close()

def delete_record():
    """Delete SDLC phase record"""
    db = connect_db()
    if not db:
        return
    
    cursor = db.cursor()
    try:
        cursor.execute("SELECT phase_name, attribute1 FROM sdlc_5")
        records = cursor.fetchall()
        
        if not records:
            print("No records found!")
            return
        
        print("\nExisting Records:")
        for i, (name, attr1) in enumerate(records, 1):
            print(f"{i}. {name} - {attr1 or 'No attributes'}")
        
        record_num = int(input("\nEnter record number to delete: ")) - 1
        if record_num < 0 or record_num >= len(records):
            print("Invalid record number!")
            return
            
        cursor.execute("SELECT id FROM sdlc_5 LIMIT 1 OFFSET %s", (record_num,))
        record_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM sdlc_5 WHERE id = %s", (record_id,))
        db.commit()
        print("Record deleted successfully!")
    except (ValueError, IndexError):
        print("Invalid input!")
    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        db.close()

def view_records():
    """View all SDLC phase records"""
    db = connect_db()
    if not db:
        return
    
    cursor = db.cursor()
    try:
        cursor.execute("""
        SELECT phase_name, attribute1, attribute2, attribute3, attribute4 
        FROM sdlc_5
        """)
        records = cursor.fetchall()
        
        if not records:
            print("No records found!")
            return
        
        print(f"\nFound {len(records)} records:")
        for i, (name, *attrs) in enumerate(records, 1):
            print(f"\nRecord {i}: {name}")
            for j, attr in enumerate(attrs, 1):
                if attr:
                    print(f"  Attribute {j}: {attr}")
    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        db.close()

def main():
    """Main program loop"""
    if not initialize_db():
        print("Failed to initialize database")
        return
    
    while True:
        print("\nSDLC Phase Management")
        print("1. Insert Record")
        print("2. Delete Record")
        print("3. View Records")
        print("4. Exit")
        
        choice = input("Enter choice (1-4): ")
        
        if choice == "1":
            insert_record()
        elif choice == "2":
            delete_record()
        elif choice == "3":
            view_records()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()