from flask import session, redirect, url_for, render_template, request
import json
from openai import OpenAI
from utils.db_connection import get_db_connection

with open('config.json') as config_file:
    config = json.load(config_file)
    key = config['KEY']

client = OpenAI(api_key=key)
model = "gpt-4o-mini"

functions_description = [{
    "name":"update_appointment",
    "description":"doctor updates the appointment of a patient",
    "parameters":{
        "type":"object",
        "properties":{
            "patient_name":{
                "type":"string",
                "description":"Name of the patient"
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
        "required":["name", "diagnosis"]
    }
}]

system_message = {
    "role": "system",
    "content": ( "You are a doctor  assistant designed to help the user keep a record of their appointments, diagnosis and medication."
                 "You must ensure that the user provides relevant information about appointments,the patient's diagnosis and medication."
                 "If the user says something irrelevant, remind them of your purpose."
                 "If the user provides a patient's name, a diagnosis and medication, call function extract_data."
                 "Never ask for user confirmation."
                 "if no medication is provided dont assume anything about it"
                 "medication is an optional field, if not provided, leave it empty"
                 "names are given in greeklish"
                 "ignore pronouns such as mr, mrs, miss, dr, etc."
                 "the diagnosis can be that the patient is healthy"
                ),
}

conversation = [system_message]

def get_appointments(doctor_id):
    query = """
        SELECT DISTINCT patients.name, available_slots.date_time, appointments.status, appointments.diagnosis, appointments.medicine, appointments.slot_id
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.patient_id
        JOIN available_slots ON appointments.slot_id = available_slots.slot_id
        WHERE appointments.doctor_id = %s AND appointments.status NOT IN ("canceled")
        ORDER BY available_slots.date_time DESC;
    """

    conn = get_db_connection("doc_feedback_user")
    cur = conn.cursor(dictionary=True)
    cur.execute(query, (doctor_id,))
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    return appointments

def update_appointment(doctor_id, appointments, patient_name, diagnosis, medication):
    corr_apps = [app for app in appointments if app["status"] == "scheduled"]
    for appointment in corr_apps:
        if patient_name.lower() in appointment["name"].lower():
            # appointment is correct
            # find patient_id
            query ="""SELECT patient_id FROM patients WHERE name = %s"""
            db = get_db_connection("doc_feedback_user")
            cursor = db.cursor(dictionary=True)
            cursor.execute(query, (appointment["name"],))
            patient_id = cursor.fetchone()["patient_id"]
            
            # update appointment
            query = """UPDATE appointments SET diagnosis = %s, medicine = %s, status = "completed"
            WHERE patient_id = %s AND slot_id = %s AND doctor_id = %s;"""

            cursor.execute(query, (diagnosis, medication, patient_id, appointment["slot_id"], doctor_id))

            query = """UPDATE patients SET medical_record = %s WHERE patient_id = %s;"""
            cursor.execute(query, (diagnosis, patient_id))

            db.commit()
            
            cursor.close()
            db.close()

            return f"Appointment for {appointment["name"]} updated successfully"
        else:
            return f"Patient {patient_name} not found"


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
    diagnosis = params["diagnosis"] if "diagnosis" in params else None
    medication = params["medication"] if "medication" in params else None
    medication = None if medication == "" else medication
    params = {
        "patient_name": params["patient_name"],
        "diagnosis": diagnosis,
        "medication": medication
    }
    return params

chat = []
def init_doctor_appointments_route(app):
    @app.route('/doctor/appointments_history', methods=['GET', 'POST'])
    def doctor_appointments():
        doctor_id = session['user_id']
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Redirect non-doctors

        
        appointments = get_appointments(doctor_id)
        # Split appointments based on diagnosis
        appointments_with_diagnosis = [appt for appt in appointments if appt["diagnosis"] is not None]  # Appointments with a diagnosis
        appointments_without_diagnosis = [appt for appt in appointments if appt["diagnosis"] is None]  # Appointments without a diagnosis

        if request.method == 'POST':
            global chat
            global conversation
            feedback = request.form['feedback']
            params = get_doctor_feedback(conversation,feedback)
            conversation.append({"role": "user", "content": feedback})
            chat.append({"role": "user", "content": feedback})
            
            if type(params) == str:
                chat.append({"role": "assistant", "content": params})
            elif type(params) == dict:
                success = update_appointment(doctor_id, appointments_without_diagnosis, **params)
                chat.append({"role": "assistant", "content": success})
                conversation = [system_message]
                # update appointments
                appointments = get_appointments(doctor_id)
                appointments_with_diagnosis = [appt for appt in appointments if appt["diagnosis"] is not None]  # Appointments with a diagnosis
                appointments_without_diagnosis = [appt for appt in appointments if appt["diagnosis"] is None]  # Appointments without a diagnosis

        return render_template('doctor_appointments.html', 
                            appointments_with_diagnosis=appointments_with_diagnosis,
                            appointments_without_diagnosis=appointments_without_diagnosis, chat=chat)