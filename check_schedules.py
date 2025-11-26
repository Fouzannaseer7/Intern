import mysql.connector

def main():
    cfg = {
        'host': 'localhost',
        'user': 'root',
        'password': 'Founas@123',
        'database': 'HospitalManagementSystem'
    }
    try:
        conn = mysql.connector.connect(**cfg)
    except Exception as e:
        print('DB connect failed:', e)
        return
    cur = conn.cursor()
    names = ['Rakesh','Pooja','Dev','Sanjay','Kirti','Nitin','Tanvi','Mohit','Kavita','Swati','Manish','Ruchi','Shreya','Abhay','Nikita']
    placeholder = ','.join(['%s']*len(names))
    sql = f"SELECT u.full_name, d.doctor_id, ds.day_of_week, ds.start_time, ds.end_time FROM users u JOIN doctors d ON u.user_id=d.user_id LEFT JOIN doctor_schedules ds ON d.doctor_id=ds.doctor_id WHERE u.full_name IN ({placeholder}) ORDER BY u.full_name, ds.day_of_week"
    cur.execute(sql, tuple(names))
    rows = cur.fetchall()
    if not rows:
        print('No schedule rows found for provided doctors.')
    else:
        for r in rows:
            print(r)
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
