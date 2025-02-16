from flask import render_template, redirect, url_for, request, session, flash
from werkzeug.security import check_password_hash
from utils.db_connection import get_db_connection 
from utils.valid_email import is_valid_email

    
def init_login_route(app):
    @app.route('/', methods=['GET', 'POST'])
    def login():
        session.clear()
        
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            if not is_valid_email(email):
                flash("Invalid email format", "danger")
                return redirect(url_for('login'))

            db = get_db_connection("login_user")
            cursor = db.cursor(dictionary=True)

            cursor.execute("""SELECT * FROM patients WHERE email = %s""", (email,))
            patient = cursor.fetchone()

            cursor.execute("""SELECT * FROM doctors WHERE email = %s""", (email,))
            doctor = cursor.fetchone()

            cursor.close()

            user = patient if patient else doctor
            user_type = "patient" if patient else "doctor" if doctor else None

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['patient_id'] if user_type == "patient" else user['doctor_id']
                session['email'] = user['email']
                session['zip_code'] = user['zip_code']
                session['street'] = user['street']
                session['user_type'] = user_type  # Store user type in session
                
                flash("Login successful!", "success")
                
                return redirect(url_for('main_page')) if user_type == "patient" else redirect(url_for('doctor_page'))
            else:
                flash("Invalid email or password", "danger")

            db.close()

        return render_template('login.html')


    @app.route('/logout')
    def logout():
        session.clear()
        flash("You have been logged out", "info")
        return redirect(url_for('login'))