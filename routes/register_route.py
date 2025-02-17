from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash
from utils.db_connection import get_db_connection 
from utils.valid_email import is_valid_email
from utils.valid_zipcode import is_valid_zip

def get_first_available_id(cursor, table_name, id_column):
    """Finds the first available ID in the given table."""
    query = f"SELECT {id_column} FROM {table_name} ORDER BY {id_column} ASC"
    cursor.execute(query)
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
            user_type = request.form['user_type']

            specialty = request.form.get('specialty') if user_type == "doctor" else None  # Only get if doctor

            if not is_valid_email(email):
                flash("Invalid email format!", "danger")
                return render_template('register.html')

            if not is_valid_zip(zip_code):
                flash("Invalid zip code!", "danger")
                return render_template('register.html')

            if not name or not email or not password or not zip_code or not street or not city:
                flash("All fields are required!", "danger")
                return render_template('register.html')

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method='pbkdf2:sha512')

            db = get_db_connection("register_user")
            cursor = db.cursor()

            # Check or create address entry
            zip_code, error = get_or_create_address(cursor, zip_code, city)
            if error:
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
                    patient_id = get_first_available_id(cursor, "patients", "patient_id")
                    cursor.execute(
                        "INSERT INTO patients (patient_id, name, email, password, zip_code, street) VALUES (%s, %s, %s, %s, %s, %s)",
                        (patient_id, name, email, hashed_password, zip_code, street)
                    )
                elif user_type == "doctor":
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
