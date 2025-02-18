from flask import render_template, request, jsonify, session, redirect, url_for
from utils.db_connection import get_db_connection
from utils.valid_zipcode import is_valid_zip
import requests
import json

def init_account_route(app):
    @app.route('/account')
    def account_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
        
        patient_id = session['user_id']
        query = """
            SELECT name, street, zip_code, age, gender, medical_record, family_history, email
            FROM patients
            WHERE patient_id = %s
        """

        conn = get_db_connection("account_user")
        cur = conn.cursor()
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()
        conn.close()

        return render_template('account.html', patient=patient)

    @app.route('/update_account', methods=['POST'])
    def update_account():
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'})

        patient_id = session['user_id']
        name = request.form.get('name')
        street = request.form.get('street')
        zip_code = request.form.get('zip_code')
        age = request.form.get('age')
        gender = request.form.get('gender')
        medical_record = request.form.get('medical_record')
        family_history = request.form.get('family_history')

        a = is_valid_zip(zip_code)
        if not a:
            return jsonify({'success': False})
        
        conn = get_db_connection("account_user")
        cur = conn.cursor()

        query = "SELECT COUNT(*) FROM address WHERE zip_code = %s"
        cur.execute(query, (zip_code,))
        
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

        update_query = """
                UPDATE patients
                SET name = %s, street = %s, zip_code = %s, age = %s, gender = %s, medical_record = %s, family_history = %s
                WHERE patient_id = %s
            """
        cur.execute(update_query, (name, street, zip_code, age, gender, medical_record, family_history, patient_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})
