import mysql.connector
from mysql.connector import errorcode

# MySQL connection configuration
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Founas@123',  # Your MySQL password here
    'database': 'sdlc_dbs'
}

def get_total_rows(cursor):
    """Return the total number of rows in the sdlc_phases table."""
    cursor.execute("SELECT COUNT(*) FROM sdlc_phases")
    return cursor.fetchone()[0]

def get_row_by_number(cursor, number):
    """Fetch the SDLC phase row by its ordinal number (1-based index)."""
    query = "SELECT * FROM sdlc_phases ORDER BY id ASC LIMIT 1 OFFSET %s"
    cursor.execute(query, (number - 1,))
    return cursor.fetchone()

def main():
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(**config)
        #conn = mysql.connector.
        cursor = conn.cursor()

        total_rows = get_total_rows(cursor)
        print(f"Total SDLC phases available: {total_rows}")

        while True:
            user_input = input(f"Enter a number (1-{total_rows}) to get the SDLC phase, or 'q' to quit: ").strip()
            if user_input.lower() == 'q':
                print("Exiting.")
                break

            if not user_input.isdigit():
                print("Invalid input. Please enter a valid number or 'q' to quit.")
                continue

            num = int(user_input)
            if num < 1 or num > total_rows:
                print("Invalid entry. Number out of range.")
                continue

            row = get_row_by_number(cursor, num)
            if row:
                print(f"\nSDLC Phase {num}:")
                print(f"ID: {row[0]}")
                print(f"Phase Name: {row[1]}")
                print(f"Attribute 1: {row[2]}")
                print(f"Attribute 2: {row[3]}")
                print(f"Attribute 3: {row[4]}")
                print(f"Attribute 4: {row[5]}\n")
            else:
                print("No data found for that number.")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied: Check your username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist.")
        else:
            print(f"MySQL Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
