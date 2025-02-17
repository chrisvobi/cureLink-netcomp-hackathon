from flask import render_template, session, redirect, url_for
from utils.db_connection import get_db_connection

def init_doctor_appointments_route(app):
    @app.route('/doctor/appointments_history')
    def doctor_appointments():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Redirect non-doctors

        doctor_id = session['user_id']
        query = """
            SELECT patients.name, available_slots.date_time, appointments.status, appointments.diagnosis, appointments.medicine
            FROM appointments
            JOIN patients ON appointments.patient_id = patients.patient_id
            JOIN available_slots ON appointments.slot_id = available_slots.slot_id
            WHERE appointments.doctor_id = %s
            ORDER BY available_slots.date_time DESC
        """

        conn = get_db_connection("appointment_history_user")
        cur = conn.cursor()
        cur.execute(query, (doctor_id,))
        appointments = cur.fetchall()
        cur.close()
        conn.close()

        return render_template('doctor_appointments.html', appointments=appointments)
