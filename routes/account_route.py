from flask import render_template, request, jsonify, session, redirect, url_for
from utils.db_connection import get_db_connection

def init_account_route(app):
    @app.route('/account')
    def account_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
        
        patient_id = session['user_id']
        query = """
            SELECT name, street, zip_code, age, gender, medical_record, family_history
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

        update_query = """
            UPDATE patients
            SET name = %s, street = %s, zip_code = %s, age = %s, gender = %s, medical_record = %s, family_history = %s
            WHERE patient_id = %s
        """

        conn = get_db_connection("account_user")
        cur = conn.cursor()
        cur.execute(update_query, (name, street, zip_code, age, gender, medical_record, family_history, patient_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})
