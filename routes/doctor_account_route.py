from flask import render_template, request, jsonify, session, redirect, url_for
from utils.db_connection import get_db_connection

def init_doctor_account_route(app):
    @app.route('/doctor_account')
    def doctor_account_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Restrict patients
        
        doctor_id = session['user_id']
        query = """
            SELECT name, email, specialty, zip_code, street
            FROM doctors
            WHERE doctor_id = %s
        """

        conn = get_db_connection("doc_account_user")
        cur = conn.cursor()
        cur.execute(query, (doctor_id,))
        doctor = cur.fetchone()
        cur.close()
        conn.close()

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

        update_query = """
            UPDATE doctors
            SET name = %s, specialty = %s, zip_code = %s, street = %s
            WHERE doctor_id = %s
        """

        conn = get_db_connection("doc_account_user")
        cur = conn.cursor()
        cur.execute(update_query, (name, specialty, zip_code, street, doctor_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})
