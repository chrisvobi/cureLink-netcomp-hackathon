from flask import render_template, session, redirect, url_for
from utils.db_connection import get_db_connection

def init_appointments_history_route(app):
    @app.route('/appointments_history')
    def appointments_history_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in
        
        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
        
        patient_id = session['user_id']

        # Query για scheduled ραντεβού
        query_scheduled = """
            SELECT doctors.name, doctors.specialty, available_slots.date_time, appointments.status, appointments.diagnosis, appointments.medicine
            FROM appointments
            JOIN doctors ON appointments.doctor_id = doctors.doctor_id
            JOIN available_slots ON appointments.slot_id = available_slots.slot_id AND appointments.doctor_id = available_slots.doctor_id
            WHERE appointments.patient_id = %s AND appointments.status = 'scheduled'
            ORDER BY available_slots.date_time DESC
        """
        
        # Query για completed ραντεβού
        query_completed = """
            SELECT doctors.name, doctors.specialty, available_slots.date_time, appointments.status, appointments.diagnosis, appointments.medicine
            FROM appointments
            JOIN doctors ON appointments.doctor_id = doctors.doctor_id
            JOIN available_slots ON appointments.slot_id = available_slots.slot_id AND appointments.doctor_id = available_slots.doctor_id
            WHERE appointments.patient_id = %s AND appointments.status = 'completed'
            ORDER BY available_slots.date_time DESC
        """

        conn = get_db_connection("appointment_history_user")
        cur = conn.cursor()

        # Εκτέλεση query για scheduled
        cur.execute(query_scheduled, (patient_id,))
        scheduled_appointments = cur.fetchall()

        # Εκτέλεση query για completed
        cur.execute(query_completed, (patient_id,))
        completed_appointments = cur.fetchall()

        cur.close()
        conn.close()

        return render_template('appointments_history.html', 
                               scheduled_appointments=scheduled_appointments, 
                               completed_appointments=completed_appointments)
