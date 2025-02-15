from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import config
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.MYSQL_HOST,
            database=config.MYSQL_DB,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD
        )
        if connection.is_connected():
            print("Successfully connected to the database")
    except Error as e:
        print(f"Error: '{e}'")
    return connection

# Route for home page, redirects to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Database connection
        conn = create_connection()
        cursor = conn.cursor()

        # Query to check if email and password match
        cursor.execute("SELECT * FROM patients WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        if user:
            flash("Welcome to CureLink!!", "success")
            return redirect(url_for('dashboard'))  # Redirect to the dashboard
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template('login.html')

# Dummy dashboard route
@app.route('/dashboard')
def dashboard():
    return "Welcome to the dashboard!"

@app.route('/register', methods=['GET', 'POST'])
# Registration route
def register():
    if request.method == 'POST':
        # Get data from form
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        zip_code = request.form['zip_code']
        city = request.form['city']
        street = request.form['street']

        # Hash the password using bcrypt
        salt = bcrypt.gensalt()  # Generate a salt for the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)  # Hash the password with the salt

        # Database connection
        conn = create_connection()
        cursor = conn.cursor()

        # Check if the zip_code already exists in the address table
        cursor.execute("SELECT * FROM address WHERE zip_code = %s", (zip_code,))
        existing_address = cursor.fetchone()

        if existing_address:
            # If the zip_code exists, use the existing city value or just proceed
            flash("This zip code already exists. You may be updating an existing address.", "info")
        else:
            # Insert the new zip_code and city into the address table
            insert_address_query = """
            INSERT INTO address (zip_code, city)
            VALUES (%s, %s)
            """
            cursor.execute(insert_address_query, (zip_code, city))
            conn.commit()  # Commit the insert
            flash("New address added to the system.", "success")

        # Insert the new patient into the patients table
        insert_patient_query = """
        INSERT INTO patients (name, email, password, zip_code, street)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(insert_patient_query, (name, email, hashed_password, zip_code, street))
            conn.commit()  # Commit the patient insert
            flash("Registration successful! Welcome to CureLink.", "success")
            return redirect(url_for('login'))  # Redirect to login page after successful registration
        except Error as e:
            print(f"Error: '{e}'")
            flash("There was an error with your registration. Please try again.", "danger")
            conn.rollback()

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
