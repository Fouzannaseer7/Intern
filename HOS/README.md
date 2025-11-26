# HospitalManagementSystem (HOS)

This repository contains a Flask-based hospital appointment system.

Quick setup (Windows / PowerShell):

1. Create a Python virtual environment and install dependencies

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

2. Create the database and schema (MySQL)

   # create database and tables
   mysql -u root -p < schema.sql

   # Create an admin user: generate a password hash in Python and insert into users table
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourAdminPassword'))"
   # use the printed value in an INSERT INTO users (...) VALUES (...) statement

3. Provide environment variables (recommended)

   $env:DB_HOST='localhost'; $env:DB_USER='root'; $env:DB_PASSWORD='secret'; $env:DB_NAME='HospitalManagementSystem'; $env:SECRET_KEY='a-long-secret'

4. Run the app

   python HOS\app.py

Notes:
- The app expects tables with lowercase names: `users`, `doctors`, `appointments`, `medical_records`, `departments`, `notifications`.
- Passwords must be stored in `users.password_hash` using Werkzeug `generate_password_hash` format.
- For production, set `SECRET_KEY` and `DB_*` env vars and run behind a proper WSGI server.
