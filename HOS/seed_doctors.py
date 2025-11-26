"""
Seed script for inserting departments, users (doctors), doctors and doctor_schedules.

Usage: python seed_doctors.py

This script uses the same DB config as `app.py` and will:
- create departments (if not exists)
- create user accounts for each doctor (password set to 'password123' - change after seeding)
- create doctors entries linked to users
- create doctor_schedules rows for availability

Notes / assumptions:
- Table names expected: `departments`, `users`, `doctors`, `doctor_schedules`.
- `users` is expected to accept columns (username, password_hash, email, user_type).
- `doctors` is expected to accept at least (user_id, specialization, department_id, years_of_experience, available_days, available_time, short_profile, photo_url).
- `doctor_schedules` is expected to accept (doctor_id, day_of_week, start_time, end_time).

If your schema is different, adapt the script accordingly.
"""

from werkzeug.security import generate_password_hash
from app import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)

DEPARTMENTS = [
    (1, 'Cardiology'),
    (2, 'Neurology'),
    (3, 'Orthopedics'),
    (4, 'Pediatrics'),
    (5, 'Dermatology'),
    (6, 'General Medicine'),
    (7, 'ENT'),
    (8, 'Ophthalmology'),
    (9, 'Gynecology'),
    (10, 'Psychiatry'),
]

DOCTORS = [
    # Cardiology (dept 1)
    dict(name='Dr. Arjun', email='arjun@hospital.com', dept='Cardiology', gender='male', available_days='Monday, Wednesday', available_time='Mon 09:00-13:00; Wed 10:00-14:00', schedules=[('Monday','09:00','13:00'),('Wednesday','10:00','14:00')], specialization='Cardiology', years=8, short_profile='Experienced cardiologist focused on interventional procedures.'),
    dict(name='Dr. Shruti', email='shruti@hospital.com', dept='Cardiology', gender='female', available_days='Tuesday, Thursday', available_time='Tue 11:00-15:00; Thu 09:00-13:00', schedules=[('Tuesday','11:00','15:00'),('Thursday','09:00','13:00')], specialization='Cardiology', years=6, short_profile='Specialist in cardiac imaging and preventive cardiology.'),
    dict(name='Dr. Rajesh', email='rajesh@hospital.com', dept='Cardiology', gender='male', available_days='Friday, Saturday', available_time='Fri 10:00-14:00; Sat 09:00-12:00', schedules=[('Friday','10:00','14:00'),('Saturday','09:00','12:00')], specialization='Cardiology', years=10, short_profile='Senior consultant with expertise in heart failure.'),
    # Neurology (dept 2)
    dict(name='Dr. Isha', email='isha@hospital.com', dept='Neurology', gender='female', available_days='Monday, Thursday', available_time='Mon 10:00-14:00; Thu 09:00-13:00', schedules=[('Monday','10:00','14:00'),('Thursday','09:00','13:00')], specialization='Neurology', years=7, short_profile='Neurologist with focus on migraine and epilepsy.'),
    dict(name='Dr. Vikram', email='vikram@hospital.com', dept='Neurology', gender='male', available_days='Tuesday, Friday', available_time='Tue 14:00-18:00; Fri 10:00-13:00', schedules=[('Tuesday','14:00','18:00'),('Friday','10:00','13:00')], specialization='Neurology', years=9, short_profile='Expert in stroke management and neurorehabilitation.'),
    dict(name='Dr. Neha', email='neha@hospital.com', dept='Neurology', gender='female', available_days='Wednesday, Saturday', available_time='Wed 08:00-12:00; Sat 09:00-12:00', schedules=[('Wednesday','08:00','12:00'),('Saturday','09:00','12:00')], specialization='Neurology', years=5, short_profile='Focus on pediatric neurology and developmental disorders.'),
    # Orthopedics (dept 3)
    dict(name='Dr. Karan', email='karan@hospital.com', dept='Orthopedics', gender='male', available_days='Monday, Wednesday', available_time='Mon 11:00-15:00; Wed 09:00-12:00', schedules=[('Monday','11:00','15:00'),('Wednesday','09:00','12:00')], specialization='Orthopedics', years=11, short_profile='Orthopedic surgeon specialized in joint replacement.'),
    dict(name='Dr. Suman', email='suman@hospital.com', dept='Orthopedics', gender='female', available_days='Tuesday, Thursday', available_time='Tue 10:00-14:00; Thu 14:00-18:00', schedules=[('Tuesday','10:00','14:00'),('Thursday','14:00','18:00')], specialization='Orthopedics', years=6, short_profile='Sports injury and arthroscopic surgery specialist.'),
    dict(name='Dr. Rahul', email='rahul@hospital.com', dept='Orthopedics', gender='male', available_days='Friday, Saturday', available_time='Fri 09:00-12:00; Sat 10:00-13:00', schedules=[('Friday','09:00','12:00'),('Saturday','10:00','13:00')], specialization='Orthopedics', years=4, short_profile='Management of fractures and outpatient care.'),
    # Pediatrics (dept 4)
    dict(name='Dr. Riya', email='riya@hospital.com', dept='Pediatrics', gender='female', available_days='Monday, Thursday', available_time='Mon 08:00-11:00; Thu 09:00-13:00', schedules=[('Monday','08:00','11:00'),('Thursday','09:00','13:00')], specialization='Pediatrics', years=5, short_profile='Pediatrician focusing on early childhood care.'),
    dict(name='Dr. Anish', email='anish@hospital.com', dept='Pediatrics', gender='male', available_days='Tuesday, Friday', available_time='Tue 10:00-14:00; Fri 08:00-12:00', schedules=[('Tuesday','10:00','14:00'),('Friday','08:00','12:00')], specialization='Pediatrics', years=7, short_profile='Experienced in neonatal and adolescent care.'),
    dict(name='Dr. Divya', email='divya@hospital.com', dept='Pediatrics', gender='female', available_days='Wednesday, Saturday', available_time='Wed 11:00-15:00; Sat 09:00-12:00', schedules=[('Wednesday','11:00','15:00'),('Saturday','09:00','12:00')], specialization='Pediatrics', years=6, short_profile='Childhood immunization and growth monitoring expert.'),
    # Dermatology (dept 5)
    dict(name='Dr. Ravi', email='ravi@hospital.com', dept='Dermatology', gender='male', available_days='Monday, Thursday', available_time='Mon 14:00-17:00; Thu 09:00-13:00', schedules=[('Monday','14:00','17:00'),('Thursday','09:00','13:00')], specialization='Dermatology', years=8, short_profile='Dermatologist with cosmetic and clinical expertise.'),
    dict(name='Dr. Nisha', email='nisha@hospital.com', dept='Dermatology', gender='female', available_days='Tuesday, Friday', available_time='Tue 13:00-17:00; Fri 10:00-13:00', schedules=[('Tuesday','13:00','17:00'),('Friday','10:00','13:00')], specialization='Dermatology', years=5, short_profile='Skin allergy and pediatric dermatology specialist.'),
    dict(name='Dr. Aman', email='aman@hospital.com', dept='Dermatology', gender='male', available_days='Wednesday, Saturday', available_time='Wed 09:00-12:00; Sat 14:00-17:00', schedules=[('Wednesday','09:00','12:00'),('Saturday','14:00','17:00')], specialization='Dermatology', years=3, short_profile='General dermatologist for outpatient care.'),
    # General Medicine (dept 6)
    dict(name='Rakesh', email='rakesh@general.com', dept='General Medicine', gender='male', available_days='Monday, Wednesday', available_time='Mon 09:00-12:00; Wed 14:00-17:00', schedules=[('Monday','09:00','12:00'),('Wednesday','14:00','17:00')], specialization='General Physician', years=7, short_profile='General physician for adult and family medicine.'),
    dict(name='Pooja', email='pooja@general.com', dept='General Medicine', gender='female', available_days='Tuesday, Thursday', available_time='Tue 10:00-13:00; Thu 15:00-18:00', schedules=[('Tuesday','10:00','13:00'),('Thursday','15:00','18:00')], specialization='General Physician', years=5, short_profile='Primary care physician focusing on preventive medicine.'),
    dict(name='Dev', email='dev@general.com', dept='General Medicine', gender='male', available_days='Monday, Friday', available_time='Mon 11:00-14:00; Fri 09:00-12:00', schedules=[('Monday','11:00','14:00'),('Friday','09:00','12:00')], specialization='General Physician', years=6, short_profile='Experienced GP with interest in chronic disease management.'),
    # ENT (dept 7)
    dict(name='Sanjay', email='sanjay@ent.com', dept='ENT', gender='male', available_days='Monday', available_time='Mon 09:00-12:00', schedules=[('Monday','09:00','12:00')], specialization='ENT', years=8, short_profile='Ear, nose and throat specialist.'),
    dict(name='Kirti', email='kirti@ent.com', dept='ENT', gender='female', available_days='Tuesday', available_time='Tue 13:00-16:00', schedules=[('Tuesday','13:00','16:00')], specialization='ENT', years=5, short_profile='ENT consultant focusing on pediatric cases.'),
    dict(name='Nitin', email='nitin@ent.com', dept='ENT', gender='male', available_days='Wednesday', available_time='Wed 10:00-13:00', schedules=[('Wednesday','10:00','13:00')], specialization='ENT', years=6, short_profile='Routine ENT procedures and outpatient care.'),
    # Ophthalmology (dept 8)
    dict(name='Tanvi', email='tanvi@oph.com', dept='Ophthalmology', gender='female', available_days='Thursday', available_time='Thu 14:00-17:00', schedules=[('Thursday','14:00','17:00')], specialization='Ophthalmology', years=7, short_profile='Eye specialist with focus on refractive care.'),
    dict(name='Mohit', email='mohit@oph.com', dept='Ophthalmology', gender='male', available_days='Friday', available_time='Fri 10:00-13:00', schedules=[('Friday','10:00','13:00')], specialization='Ophthalmology', years=6, short_profile='General ophthalmologist for outpatient services.'),
    dict(name='Kavita', email='kavita@oph.com', dept='Ophthalmology', gender='female', available_days='Saturday', available_time='Sat 09:00-12:00', schedules=[('Saturday','09:00','12:00')], specialization='Ophthalmology', years=5, short_profile='Experienced in cataract and glaucoma screenings.'),
    # Gynecology (dept 9)
    dict(name='Swati', email='swati@gyn.com', dept='Gynecology', gender='female', available_days='Monday', available_time='Mon 09:00-11:30', schedules=[('Monday','09:00','11:30')], specialization='Gynecology', years=8, short_profile='Obstetrician and gynecologist.'),
    dict(name='Manish', email='manish@gyn.com', dept='Gynecology', gender='male', available_days='Tuesday', available_time='Tue 12:00-15:00', schedules=[('Tuesday','12:00','15:00')], specialization='Gynecology', years=7, short_profile='Women health and laparoscopy specialist.'),
    dict(name='Ruchi', email='ruchi@gyn.com', dept='Gynecology', gender='female', available_days='Friday', available_time='Fri 10:00-13:00', schedules=[('Friday','10:00','13:00')], specialization='Gynecology', years=6, short_profile='Specialist in maternal health and prenatal care.'),
    # Psychiatry (dept 10)
    dict(name='Shreya', email='shreya@psych.com', dept='Psychiatry', gender='female', available_days='Wednesday', available_time='Wed 10:00-13:00', schedules=[('Wednesday','10:00','13:00')], specialization='Psychiatry', years=9, short_profile='Psychiatrist focusing on mood disorders.'),
    dict(name='Abhay', email='abhay@psych.com', dept='Psychiatry', gender='male', available_days='Thursday', available_time='Thu 14:00-17:00', schedules=[('Thursday','14:00','17:00')], specialization='Psychiatry', years=8, short_profile='Clinical psychiatrist with therapy experience.'),
    dict(name='Nikita', email='nikita@psych.com', dept='Psychiatry', gender='female', available_days='Saturday', available_time='Sat 09:00-12:00', schedules=[('Saturday','09:00','12:00')], specialization='Psychiatry', years=5, short_profile='Child and adolescent psychiatry specialist.'),
]

# Alternate photos for variety
PHOTO_FALLBACKS = {
    'male': [
        'static/img/male1.jpg',
        'static/img/male2.jpg',
        'static/img/male3.jpg',
    ],
    'female': [
        'static/img/female1.jpg',
        'static/img/female2.jpg',
        'static/img/female3.jpg',
    ]
}


def ensure_departments(conn):
    with conn.cursor() as cursor:
        for dept_id, name in DEPARTMENTS:
            # Try to find by name first
            cursor.execute("SELECT department_id FROM departments WHERE name = %s", (name,))
            row = cursor.fetchone()
            if row:
                logging.info('Department exists: %s -> id=%s', name, row[0])
                continue
            try:
                cursor.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
                conn.commit()
                logging.info('Inserted department: %s', name)
            except Exception as e:
                logging.exception('Failed to insert department %s: %s', name, e)


def get_or_create_user(conn, name, email, password='password123'):
    username = email.split('@')[0]
    pw_hash = generate_password_hash(password)
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        if row:
            return row[0]
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, email, user_type, full_name, is_active) VALUES (%s, %s, %s, 'doctor', %s, TRUE)",
                (username, pw_hash, email, name)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            # Try without full_name column (some schemas don't have it)
            try:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email, user_type) VALUES (%s, %s, %s, 'doctor')",
                    (username, pw_hash, email)
                )
                conn.commit()
                return cursor.lastrowid
            except Exception:
                logging.exception('Failed to create user for %s (%s)', name, email)
                return None


def find_department_id(conn, dept_name):
    with conn.cursor() as cursor:
        cursor.execute("SELECT department_id FROM departments WHERE name = %s", (dept_name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return None


def create_doctor(conn, user_id, doc, dept_id, photo_path):
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO doctors (user_id, specialization, department_id, years_of_experience, available_days, available_time, short_profile, photo_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, doc['specialization'], dept_id, doc['years'], doc['available_days'], doc['available_time'], doc.get('short_profile'), photo_path)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            logging.warning('Insert with full columns failed for %s, trying fallback inserts', doc['name'])
            try:
                # Try without short_profile
                cursor.execute(
                    "INSERT INTO doctors (user_id, specialization, department_id, years_of_experience, available_days, available_time, photo_url) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (user_id, doc['specialization'], dept_id, doc['years'], doc['available_days'], doc['available_time'], photo_path)
                )
                conn.commit()
                return cursor.lastrowid
            except Exception:
                logging.warning('Insert without short_profile failed for %s, trying minimal insert', doc['name'])
                try:
                    # Minimal insert: some schemas only have basic columns
                    cursor.execute(
                        "INSERT INTO doctors (user_id, specialization, department_id, years_of_experience) VALUES (%s, %s, %s, %s)",
                        (user_id, doc['specialization'], dept_id, doc['years'])
                    )
                    conn.commit()
                    return cursor.lastrowid
                except Exception:
                    logging.exception('Failed to insert doctor %s after fallbacks', doc['name'])
                    return None


def create_schedules(conn, doctor_id, schedules):
    with conn.cursor() as cursor:
        for day, start, end in schedules:
            try:
                cursor.execute(
                    "INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s)",
                    (doctor_id, day, start, end)
                )
            except Exception:
                logging.exception('Failed to insert schedule %s for doctor_id=%s', day, doctor_id)
        conn.commit()


def main():
    conn = get_db_connection()
    if not conn:
        logging.error('DB connection failed')
        return

    try:
        ensure_departments(conn)
        # optional clear: if --clear passed, remove schedules for these departments first
        import sys
        if '--clear' in sys.argv:
            logging.info('Clearing existing doctor schedules for seeded departments...')
            # find department ids for our DEPARTMENTS list
            dept_names = [d[1] for d in DEPARTMENTS]
            with conn.cursor() as cursor:
                # get department ids
                cursor.execute("SELECT department_id FROM departments WHERE name IN (%s)" % (', '.join(['%s']*len(dept_names))), tuple(dept_names))
                dept_rows = cursor.fetchall()
                dept_ids = [r[0] for r in dept_rows]
                if dept_ids:
                    # delete schedules for doctors in these departments
                    cursor.execute("DELETE ds FROM doctor_schedules ds JOIN doctors d ON ds.doctor_id = d.doctor_id WHERE d.department_id IN (%s)" % (', '.join(['%s']*len(dept_ids))), tuple(dept_ids))
                    conn.commit()
                    logging.info('Deleted schedules for departments: %s', dept_ids)

        # counters to give different photos to doctors of the same gender
        male_i = 0
        female_i = 0

        for idx, doc in enumerate(DOCTORS):
            logging.info('Processing %s', doc['name'])
            user_id = get_or_create_user(conn, doc['name'], doc['email'])
            if not user_id:
                logging.error('Skipping doctor %s due to user creation failure', doc['name'])
                continue

            dept_id = find_department_id(conn, doc['dept'])
            if not dept_id:
                logging.warning('Department %s not found for %s; skipping', doc['dept'], doc['name'])
                continue

            # choose a gender-aware photo if gender provided, otherwise fallback round-robin
            photo = None
            gender = doc.get('gender')
            if gender and gender in PHOTO_FALLBACKS:
                if gender == 'male':
                    photo = PHOTO_FALLBACKS['male'][male_i % len(PHOTO_FALLBACKS['male'])]
                    male_i += 1
                else:
                    photo = PHOTO_FALLBACKS['female'][female_i % len(PHOTO_FALLBACKS['female'])]
                    female_i += 1
            else:
                # round-robin across both lists
                combined = PHOTO_FALLBACKS['male'] + PHOTO_FALLBACKS['female']
                photo = combined[idx % len(combined)]
            doctor_id = create_doctor(conn, user_id, doc, dept_id, photo)
            if doctor_id and doc.get('schedules'):
                create_schedules(conn, doctor_id, doc['schedules'])

        logging.info('Seeding complete')
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
