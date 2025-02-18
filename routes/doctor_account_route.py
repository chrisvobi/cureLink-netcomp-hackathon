from flask import render_template, request, jsonify, session, redirect, url_for
from utils.db_connection import get_db_connection
from utils.valid_zipcode import is_valid_zip
import json
import requests


def init_doctor_account_route(app):
    @app.route('/doctor_account')
    def doctor_account_page():
        if 'user_id' not in session:
            return redirect(url_for('login')) # Redirect if not logged in

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Redirect doctors away
        
        # Query to get doctors account data
        query = """
            SELECT name, email, specialty, zip_code, street, pwd_accessible
            FROM doctors
            WHERE doctor_id = %s
        """

        # Establish connection with database and fetch information for the account of the doctor
        conn = get_db_connection("doc_account_user")
        cur = conn.cursor()
        cur.execute(query, (session['user_id'],))
        doctor = cur.fetchone()
        cur.close()
        conn.close()

        # Change pwd_accesible from 0/1 to no/yes
        if doctor:
            doctor = list(doctor)
            doctor[5] = "yes" if doctor[5] == 1 else "no"

        return render_template('doctor_account.html', doctor=doctor)


    @app.route('/update_doctor_account', methods=['POST'])
    def update_doctor_account():
        if 'user_id' not in session:
            return redirect(url_for('login')) # Redirect if not logged in

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Redirect doctors away

        # Get updated data from the web page
        name = request.form.get('name')
        specialty = request.form.get('specialty')
        zip_code = request.form.get('zip_code')
        street = request.form.get('street')
        pwd_accessible = request.form.get('pwd_accessible')

        # Check if the given zip code is valid
        valid_zip_code = is_valid_zip(zip_code)
        if not valid_zip_code:
            return jsonify({'success': False})
        
        # Connect to database
        conn = get_db_connection("doc_account_user")
        cur = conn.cursor()

        # Check if the given zip code already exists in the database
        query = "SELECT COUNT(*) FROM address WHERE zip_code = %s"
        cur.execute(query, (zip_code,))
        result = cur.fetchone()[0]

        # If it doesn't exist in the database
        if result == 0: 
            # Load google API key
            with open('config.json') as config_file:
                config = json.load(config_file)
                GOOGLE_API_KEY = config['GOOGLE_API_KEY']
            
            # Connect with the google maps API and fetch the zip codes correspodning city
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={zip_code}&components=country:GR&key={GOOGLE_API_KEY}"
            response = requests.get(url)
            data = response.json()
            city = data["results"][0]["address_components"][2]["long_name"]

            # Insert zip code and city into database
            insert_query = "INSERT INTO address (zip_code, city) VALUES (%s, %s)"
            cur.execute(insert_query, (zip_code, city))
            conn.commit()

        # Convert no/yes" to 0/1 for the database
        pwd_accessible = 1 if pwd_accessible == "yes" else 0

        # Query to update doctors account information
        update_query = """
            UPDATE doctors
            SET name = %s, specialty = %s, zip_code = %s, street = %s, pwd_accessible = %s
            WHERE doctor_id = %s
        """
        cur.execute(update_query, (name, specialty, zip_code, street, pwd_accessible, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})
