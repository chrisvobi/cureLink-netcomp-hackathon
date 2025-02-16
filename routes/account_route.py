from flask import render_template, session, redirect, url_for
from utils.db_connection import get_db_connection  # Ensure this module is correctly implemented

def init_account_route(app):
    @app.route('/account')
    def account_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in

        patient_id = session['user_id']  # Get the logged-in user's ID
        query = """
            SELECT name, street, age, gender, medical_record, family_history
            FROM patients
            WHERE patient_id = %s
        """

        conn = get_db_connection("account_user")
        cur = conn.cursor()
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()
        conn.close()

        return render_template('account.html', patient=patient)  # Pass data to the template
