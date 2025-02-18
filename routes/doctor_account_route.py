from flask import render_template, request, jsonify, session, redirect, url_for
from utils.db_connection import get_db_connection
from utils.valid_zipcode import is_valid_zip
import json
import requests

def init_doctor_account_route(app):
    @app.route('/doctor_account')
    def doctor_account_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Restrict patients
        
        doctor_id = session['user_id']
        query = """
            SELECT name, email, specialty, zip_code, street, pwd_accessible
            FROM doctors
            WHERE doctor_id = %s
        """

        conn = get_db_connection("doc_account_user")
        cur = conn.cursor()
        cur.execute(query, (doctor_id,))
        doctor = cur.fetchone()
        cur.close()
        conn.close()

        if doctor:
            doctor = list(doctor)
            doctor[5] = "yes" if doctor[5] == 1 else "no"  # Convert to yes/no

        return render_template('doctor_account.html', doctor=doctor)

    @app.route('/update_doctor_account', methods=['POST'])
    def update_doctor_account():
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'})

        doctor_id = session['user_id']
        name = request.form.get('name')
        specialty = request.form.get('specialty')
        zip_code = request.form.get('zip_code')
        street = request.form.get('street')
        pwd_accessible = request.form.get('pwd_accessible')

        a = is_valid_zip(zip_code)
        if not a:
            return jsonify({'success': False})
        
        conn = get_db_connection("doc_account_user")
        cur = conn.cursor()

        query = "SELECT COUNT(*) FROM address WHERE zip_code = %s"
        cur.execute(query, (zip_code,))
        print(zip_code)
        # Fetch result
        result = cur.fetchone()[0]
        if result == 0:
            with open('config.json') as config_file:
                config = json.load(config_file)
                GOOGLE_API_KEY = config['GOOGLE_API_KEY']
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={zip_code}&components=country:GR&key={GOOGLE_API_KEY}"
            response = requests.get(url)
            data = response.json()
            city = data["results"][0]["address_components"][2]["long_name"]
            insert_query = "INSERT INTO address (zip_code, city) VALUES (%s, %s)"
            cur.execute(insert_query, (zip_code, city))
            conn.commit()

        # Convert "yes"/"no" to 1/0 for the database
        pwd_accessible = 1 if pwd_accessible == "yes" else 0

        update_query = """
            UPDATE doctors
            SET name = %s, specialty = %s, zip_code = %s, street = %s, pwd_accessible = %s
            WHERE doctor_id = %s
        """

        conn = get_db_connection("doc_account_user")
        cur = conn.cursor()
        cur.execute(update_query, (name, specialty, zip_code, street, pwd_accessible, doctor_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})
