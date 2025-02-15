from flask import render_template, redirect, url_for, request, flash
import mysql.connector
from werkzeug.security import generate_password_hash
import json

def get_db_connection():
    # Load database configuration
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    db_user = config["register_user"]

    # Connect to MySQL
    db = mysql.connector.connect(
        host=config["host"],
        user=db_user["user"],
        password=db_user["password"],
        database=config["database"]
    )

    return db

def get_first_available_patient_id(cursor):
    """Finds the first available patient_id in the patients table."""
    cursor.execute("SELECT patient_id FROM patients ORDER BY patient_id ASC")
    existing_ids = [row[0] for row in cursor.fetchall()]
    
    # Find the smallest missing number in the sequence
    expected_id = 1
    for existing_id in existing_ids:
        if existing_id == expected_id:
            expected_id += 1
        else:
            break
    return expected_id

def get_or_create_address(cursor, zip_code, city):
    """Checks if the zip code exists in the address table. If not, inserts it."""
    
    # Check if zip code exists
    cursor.execute("SELECT  city FROM address WHERE zip_code = %s", (zip_code,))
    address = cursor.fetchone()

    if address:
        # If zip code exists but city does not match, return an error
        if address[0] != city:
            return None, "Zip code exists but city does not match!"
        return zip_code, None

    # If zip code does not exist, insert new address
    cursor.execute("INSERT INTO address (zip_code, city) VALUES (%s, %s)", (zip_code, city))
    return zip_code, None

def init_register_route(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            zip_code = request.form['zip_code']
            street = request.form['street']
            city = request.form['city']

            if not name or not email or not password or not zip_code or not street or not city:
                flash("All fields are required!", "danger")
                return render_template('register.html')
            # Hash the password before storing it
            hashed_password = password

            db = get_db_connection()
            if db is None:
                flash("Database connection failed!", "danger")
                return render_template('register.html')
            cursor = db.cursor()

            # Check or create address entry
            zip_code, error = get_or_create_address(cursor, zip_code, city)
            if error:
                flash(error, "danger")
                cursor.close()
                db.close()
                return render_template('register.html')
            
            # Check if the email already exists
            cursor.execute("SELECT * FROM patients WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Email is already registered. Please log in.", "danger")
            else:

                patient_id = get_first_available_patient_id(cursor)

                cursor.execute(
                    "INSERT INTO patients (patient_id, name, email, password, zip_code, street) VALUES (%s, %s, %s, %s, %s, %s)",
                    (patient_id, name, email, hashed_password, zip_code, street)
                )
                db.commit()
                flash("Registration successful! You can now log in.", "success")
                return redirect(url_for('login'))

            cursor.close()
            db.close()

        return render_template('register.html')
