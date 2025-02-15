from flask import render_template, redirect, url_for, request, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import json

def get_db_connection():
    # Load database configuration from JSON file
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    db_user = config["login_user"]
    # Connect to MySQL
    db = mysql.connector.connect(
        host=config["host"],
        user=db_user["user"],
        password=db_user["password"],
        database=config["database"]
    )

    return db
    

def init_login_route(app):
    @app.route('/', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patients WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if user and user['password'] == password: #HAHASHAHAHHAHAHHAHAHAHHAHAHASHSHAHASHASHSAHhsA
                session['user_id'] = user['patient_id']
                session['email'] = user['email']
                flash("Login successful!", "success")
                return redirect(url_for('main_page'))
            else:
                flash("Invalid email or password", "danger")

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash("You have been logged out", "info")
        return redirect(url_for('login'))