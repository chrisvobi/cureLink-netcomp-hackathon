from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash
from utils.db_connection import get_db_connection 
from utils.valid_email import is_valid_email
from utils.valid_zipcode import is_valid_zip


def get_first_available_id(cursor, table_name, id_column):
    # Get all existing ids in the database
    query = f"SELECT {id_column} FROM {table_name} ORDER BY {id_column} ASC"
    cursor.execute(query)
    existing_ids = [row[0] for row in cursor.fetchall()]

    # Find the smallest missing number
    available_id = 1
    for existing_id in existing_ids:
        if existing_id == available_id:
            available_id += 1
        else:
            break
    return available_id

def get_or_create_address(cursor, zip_code, city):
    # Check if zip code exists in the database
    cursor.execute("SELECT  city FROM address WHERE zip_code = %s", (zip_code,))
    address = cursor.fetchone()

    if address:
        # If zip code exists but city does not match, return an error
        if address[0] != city:
            return None, "Zip code exists but city does not match!"
        # If zip code exists and city does match, return no error
        return zip_code, None

    # If zip code does not exist, insert new address 
    cursor.execute("INSERT INTO address (zip_code, city) VALUES (%s, %s)", (zip_code, city))
    return zip_code, None


def init_register_route(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            # Get data from the web page
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            zip_code = request.form['zip_code']
            street = request.form['street']
            city = request.form['city']
            user_type = request.form['user_type']
            specialty = request.form.get('specialty') if user_type == "doctor" else None  # Only get if doctor
            age = request.form.get('age') if user_type == "patient" else None
            gender = request.form.get('gender') if user_type == "patient" else None

            # Check if email is valid
            if not is_valid_email(email):
                flash("Invalid email format!", "danger")
                return render_template('register.html')

            # Check if zip code is valid
            if not is_valid_zip(zip_code):
                flash("Invalid zip code!", "danger")
                return render_template('register.html')

            # Check if all fields are filled
            if not name or not email or not password or not zip_code or not street or not city or not age:
                flash("All fields are required!", "danger")
                return render_template('register.html')

            # Hash the password to store it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha512')

            # Connect to database with appropriate user
            db = get_db_connection("register_user")
            cursor = db.cursor()

            # Check or create address in the database
            zip_code, error = get_or_create_address(cursor, zip_code, city)
            if error: # Throw error if zip code and city don't match
                flash(error, "danger")
                cursor.close()
                db.close()
                return render_template('register.html')

            # Check if the email already exists in patients or doctors
            cursor.execute("SELECT * FROM patients WHERE email = %s", (email,))
            existing_patient = cursor.fetchone()
            cursor.execute("SELECT * FROM doctors WHERE email = %s", (email,))
            existing_doctor = cursor.fetchone()

            if existing_patient or existing_doctor:
                flash("Email is already registered. Please log in.", "danger")
            else:
                if user_type == "patient":
                    # Save user in the patients table
                    patient_id = get_first_available_id(cursor, "patients", "patient_id")
                    cursor.execute(
                        "INSERT INTO patients (patient_id, name, email, password, zip_code, street, age, gender) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (patient_id, name, email, hashed_password, zip_code, street, age, gender)
                    )
                elif user_type == "doctor":
                    # Save user in the doctors table
                    doctor_id = get_first_available_id(cursor, "doctors", "doctor_id")
                    cursor.execute(
                        "INSERT INTO doctors (doctor_id, name, email, password, zip_code, street, specialty) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (doctor_id, name, email, hashed_password, zip_code, street, specialty)
                    )
                db.commit()
                flash("Registration successful! You can now log in.", "success")
                return redirect(url_for('login'))

            cursor.close()
            db.close()

        return render_template('register.html')
