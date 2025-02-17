from flask import session, redirect, url_for, render_template, request
import json
from openai import OpenAI
from datetime import datetime, timedelta
from utils.db_connection import get_db_connection

with open('config.json') as config_file:
    config = json.load(config_file)
    key = config['KEY']

client = OpenAI(api_key=key)
model = "gpt-4o-mini"

functions_description = [{
    "name":"extract_data",
    "description":"Extract parameters from user input",
    "parameters":{
        "type":"object",
        "properties":{
            "name":{
                "type":"string",
                "description":"Name of the patient"
            },
            "date_time":{
                "type":"string",
                "description":"Date and time of the appointment (YYYY-MM-DD HH:MM)"
            },
            "diagnosis":{
                "type":"string",
                "description":"Diagnosis of the patient"
            },
            "medication":{
                "type":"string",
                "description":"Medication prescribed to the patient"
            },
        },
        "required":["name","date_time"]
    }
}]

system_message = {
    "role": "system",
    "content": ( "You are a doctor  assistant designed to help the user keep a record of their appointments, diagnosis and medication."
                 "You must ensure that the user provides relevant information about appointments,the patient's diagnosis and medication."
                 "If the user says something irrelevant, remind them of your purpose."
                 "If the user provides a patient's name, a date and a time, a diagnosis and medication, call function extract_data."
                 "Never ask for user confirmation."
                ),
}

conversation = [system_message]


def get_doctor_feedback(conversation,user_message):
    completion = client.beta.chat.completions.parse(
        model=model,
        messages = conversation + [{"role": "user", "content": user_message}],
        functions = functions_description,
        function_call = "auto",)
    output = completion.choices[0].message
    if output.function_call is None:
        return output.content
    params = json.loads(output.function_call.arguments)
    patient_name = params["name"]
    date_time = params["date_time"]
    diagnosis = params["diagnosis"]
    medication = params["medication"]
    return patient_name, date_time, diagnosis, medication

def check_patient(patient_name, date_time, doctor_id):
    query = """
        SELECT *
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.patient_id
        JOIN available_slots ON appointments.slot_id = available_slots.slot_id AND appointments.doctor_id = available_slots.doctor_id
        WHERE patients.name = %s
        AND available_slots.date_time = %s
        AND appointments.doctor_id = %s;
    """
    conn = get_db_connection("doc_feedback_user")
    cur = conn.cursor()
    cur.execute(query, (patient_name, date_time, doctor_id))
    result = cur.fetchall()
    cur.close()
    conn.close()
    print(result)
    if result:
        return result[0][0],result[0][2] 
    else:
        return False, False; # Returns True if an appointment exists, False otherwise

def get_appointments():
    doctor_id = session['user_id']
    query = """
        SELECT DISTINCT patients.name, available_slots.date_time, appointments.status, appointments.diagnosis, appointments.medicine
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.patient_id
        JOIN available_slots ON appointments.slot_id = available_slots.slot_id
        WHERE appointments.doctor_id = %s
        ORDER BY available_slots.date_time DESC;
    """

    conn = get_db_connection("doc_feedback_user")
    cur = conn.cursor()
    cur.execute(query, (doctor_id,))
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    return appointments

def init_doctor_appointments_route(app):
    @app.route('/doctor/appointments_history', methods=['GET', 'POST'])
    def doctor_appointments():
        doctor_id = session['user_id']
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Redirect non-doctors

        
        appointments = get_appointments()
        # Split appointments based on diagnosis
        appointments_with_diagnosis = [appt for appt in appointments if appt[3] != None]  # Appointments with a diagnosis
        appointments_without_diagnosis = [appt for appt in appointments if appt[3] == None]  # Appointments without a diagnosis

        if request.method == 'POST':
            feedback = request.form['feedback']
            patient_name, date_time, diagnosis, medication = get_doctor_feedback(conversation, feedback)
            
            if patient_name and date_time:
                patient_id, slot_id = check_patient(patient_name, date_time, doctor_id)
                
                if patient_id:
                    # Update appointment status with diagnosis and medication
                    update_query = """
                        UPDATE appointments 
                        SET status = 'completed', diagnosis = %s, medicine = %s
                        WHERE patient_id = %s AND doctor_id = %s AND slot_id = %s;
                    """
                    conn = get_db_connection("doc_feedback_user")
                    cur = conn.cursor()
                    cur.execute(update_query, (diagnosis, medication, patient_id, doctor_id, slot_id))
                    conn.commit()
                    cur.close()
                    conn.close()

                    appointments = get_appointments()
                    # Split appointments based on diagnosis
                    appointments_with_diagnosis = [appt for appt in appointments if appt[3] != None]  # Appointments with a diagnosis
                    appointments_without_diagnosis = [appt for appt in appointments if appt[3] == None]  # Appointments without a diagnosis

                    return render_template('doctor_appointments.html', 
                                        appointments_with_diagnosis=appointments_with_diagnosis,
                                        appointments_without_diagnosis=appointments_without_diagnosis, 
                                        success=True)
                else:
                    pass

            return render_template('doctor_appointments.html', 
                                appointments_with_diagnosis=appointments_with_diagnosis,
                                appointments_without_diagnosis=appointments_without_diagnosis, 
                                error="Invalid data provided or no appointment found.")

        return render_template('doctor_appointments.html', 
                            appointments_with_diagnosis=appointments_with_diagnosis,
                            appointments_without_diagnosis=appointments_without_diagnosis)