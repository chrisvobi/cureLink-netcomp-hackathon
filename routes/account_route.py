from flask import render_template, request, jsonify, session, redirect, url_for
from utils.db_connection import get_db_connection
from utils.valid_zipcode import is_valid_zip
import requests
import json


def init_account_route(app):
    @app.route('/account') # View your patient account
    def account_page():
        if 'user_id' not in session:
            return redirect(url_for('login')) # Redirect if not logged in

        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
    
        # Query to get patients account data
        query = """
            SELECT name, street, zip_code, age, gender, medical_record, family_history, email
            FROM patients
            WHERE patient_id = %s
        """

        # Establish connection with database and fetch information for the account of the patient
        conn = get_db_connection("account_user")
        cur = conn.cursor()
        cur.execute(query, (session['user_id'],))
        patient = cur.fetchone()
        cur.close()
        conn.close()

        return render_template('account.html', patient=patient)


    @app.route('/update_account', methods=['POST'])
    def update_account():
        if 'user_id' not in session:
            return redirect(url_for('login')) # Redirect if not logged in

        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away

        # Get updated data from the web page
        name = request.form.get('name')
        email = request.form.get('email')
        street = request.form.get('street')
        zip_code = request.form.get('zip_code')
        age = request.form.get('age')
        gender = request.form.get('gender')
        medical_record = request.form.get('medical_record')
        family_history = request.form.get('family_history')

        # Check if the given zip code is valid
        valid_zip_code = is_valid_zip(zip_code)
        if not valid_zip_code:
            return jsonify({'success': False})
        
        # Connect to database
        conn = get_db_connection("account_user")
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

        # Query to update patients account information
        update_query = """
            UPDATE patients
            SET name = %s, email = %s, street = %s, zip_code = %s, age = %s, gender = %s, medical_record = %s, family_history = %s
            WHERE patient_id = %s
        """
        cur.execute(update_query, (name, email, street, zip_code, age, gender, medical_record, family_history, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})
