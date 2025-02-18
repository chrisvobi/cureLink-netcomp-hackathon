from flask import render_template, session, redirect, url_for, request
import math
import requests
import json
from utils.db_connection import get_db_connection
from datetime import datetime 
from openai import OpenAI

def choose_appointment (name, date_time, doctors):
    if name is None: return "Please provide a doctor's name."
    if date_time is None: return "Please provide a date and time for the appointment."
    for doctor in doctors:
        if name.lower() not in doctor['name'].lower(): return f"{name} is not available. Please choose another doctor."
        else:
            if date_time not in doctor['available_slots']: return f"Sorry, I couldn't find an available slot for {name} at {date_time}. Make sure you chose right."
        return {"doctor_id": doctor['doctor_id'], "date_time": date_time}

def book_appointment(patient_id, appointment):
    db = get_db_connection("appointment_user")
    if db is None:
        return
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT slot_id from available_slots
    where doctor_id = %s and date_time = %s
"""
    cursor.execute(query, (appointment['doctor_id'], appointment['date_time']))
    slot_id = cursor.fetchone()

    query = """
    INSERT INTO appointments (patient_id, doctor_id, slot_id, status)
    VALUES (%s, %s, %s, %s)
"""
    cursor.execute(query, (patient_id, appointment['doctor_id'], slot_id['slot_id'], "scheduled"))

    query = """
    UPDATE available_slots
    SET booked = 1
    WHERE slot_id = %s
"""
    cursor.execute(query, (slot_id['slot_id'],))
    db.commit()
    cursor.close()
    db.close()

    return f"Appointment at {appointment['date_time']} has been booked successfully."


semianswer = ""
def agent_choose_book_appointment(conversation, user_message, doctors):
    """openai model to choose appointments"""
    global semianswer
    completion = client.beta.chat.completions.parse(
        model=model,
        messages = conversation + [{"role": "user", "content": user_message + semianswer}],
        functions = functions_description,
        function_call = "auto",)
    output = completion.choices[0].message
    if output.function_call is None:
        return output.content
    params = json.loads(output.function_call.arguments)

    if output.function_call.name == "missing_name":
        semianswer = params["date_time"]
    elif output.function_call.name == "missing_date":
        semianswer = params["name"]
    
    name = params["name"] if "name" in params else None
    date_time = params["date_time"] if "date_time" in params else None

    params = {"name": name, "date_time": date_time}
    
    appointment = choose_appointment (params["name"], params["date_time"], doctors)
    if type(appointment) == str:
        book = appointment
    elif type(appointment) == dict:
        patient_id = session["user_id"]
        book = book_appointment(patient_id, appointment)

    return book


# Load API key
with open('config.json') as config_file:
    config = json.load(config_file)
    key = config['KEY']

client = OpenAI(api_key=key)
model = "gpt-4o-mini"
# Define the Pydantic model for structured output

system_message = {
    "role": "system",
    "content": ( "You are an appointmentbooking assistant designed to help the user book an appointment."
        "Your goal is to help the user choose and book an appointment in a structured database. "
        "You ensure accurate data entry, prevent duplicate entries, validate appointment times, and format the data correctly."
        "Your responses should be clear, concise, and professional."
        f"today's date is {datetime.today().strftime('%Y-%m-%d')}"
        "if the year is not provided, assume it is the current year"
        "if the month is not provided, assume it is the current month"
        "Yoy make good assumptions dont ask again"
        "if year or month have already passed, ask for clarification"
        "if user says something irrelevant remind them your purpose"
        "if user provides a doctor name, a date and a time, call function extract_data"
        "if user provides just a name call function missing_date"
        "if user provides just a date and time call function missing_name"
        "Never ask for user confirmation"
        "doctor's names are in greeklish"
        "dont tell the user what you are doing just do it"
    ),
}

conversation = [system_message]

functions_description = [{
    "name":"extract_data",
    "description":"Extract parameters from user input",
    "parameters":{
        "type":"object",
        "properties":{
            "name":{
                "type":"string",
                "description":"Name of the doctor"
            },
            "date_time":{
                "type":"string",
                "description":"Date and time of the appointment (YYYY-MM-DD HH:MM)"
            }
        },
        "required":["name","date_time"]
    }
},
{
    "name":"missing_date",
    "description":"Extract parameters from user input, just the name",
    "parameters":{
        "type":"object",
        "properties":{
            "name":{
                "type":"string",
                "description":"Name of the doctor"
            },
            "date_time":{
                "type":"string",
                "description":"Date and time of the appointment (YYYY-MM-DD HH:MM)"
            }
        },
        "required":["name"]
    }
},
{
    "name":"missing_name",
    "description":"Extract parameters from user input just the date",
    "parameters":{
        "type":"object",
        "properties":{
            "name":{
                "type":"string",
                "description":"Name of the doctor"
            },
            "date_time":{
                "type":"string",
                "description":"Date and time of the appointment (YYYY-MM-DD HH:MM)"
            }
        },
        "required":["date_time"]
    }
}]


with open('config.json') as config_file:
    config = json.load(config_file)
    GOOGLE_API_KEY = config['GOOGLE_API_KEY']

def get_coordinates(address):
    """Χρησιμοποιεί το Google Geocoding API για να μετατρέψει μια διεύθυνση σε γεωγραφικές συντεταγμένες."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data and "results" in data and len(data["results"]) > 0:
        location = data["results"][0]["geometry"]["location"]
        return location['lat'], location['lng']  # (lat, lon)
    else:
        print(f"Coordinates not found for: {address}")
        return None, None

def haversine(lat1, lon1, lat2, lon2):
    """Υπολογίζει τη γεωδαιτική απόσταση μεταξύ δύο σημείων με τον τύπο Haversine."""
    R = 6371  # Ακτίνα της Γης σε χιλιόμετρα
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Απόσταση σε χιλιόμετρα

def find_doctors_by_criteria(specialty):
    # Get patient data from session and calculate coordinates
    
    """Ανακτά και εμφανίζει γιατρούς με βάση την πόλη και την ειδικότητα, ταξινομημένους κατά απόσταση από τον ασθενή."""
    db = get_db_connection("appointment_user")
    if db is None:
        return

    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT city 
        FROM address 
        WHERE address.zip_code = %s
    """, (session['zip_code'],))
    patient_data = cursor.fetchone()

    patient_address = f"{session['street']} { patient_data['city']} {session['zip_code']}"
    patient_city =  patient_data['city']
    patient_lat, patient_lon = get_coordinates(patient_address)
    query = """
    SELECT d.doctor_id, d.name, d.specialty, d.zip_code, d.street, addr.city, d.pwd_accessible,
           GROUP_CONCAT(aslot.date_time ORDER BY aslot.date_time SEPARATOR ', ') AS available_slots
    FROM doctors d
    LEFT JOIN available_slots aslot ON d.doctor_id = aslot.doctor_id AND aslot.booked = 0
    LEFT JOIN address addr ON d.zip_code = addr.zip_code
    WHERE d.specialty = %s AND addr.city = %s
    GROUP BY d.doctor_id, d.name, d.specialty, d.zip_code, d.street, addr.city
    """
    cursor.execute(query, (specialty, patient_city))
    
    doctors = cursor.fetchall()
    doctor_distances = []

    for doctor in doctors:
        doctor_address = f"{doctor['street']} {doctor['city']} {doctor['zip_code']}"
        doctor_lat, doctor_lon = get_coordinates(doctor_address)

        if doctor_lat is not None and doctor_lon is not None:
            distance = haversine(patient_lat, patient_lon, doctor_lat, doctor_lon)
            doctor["distance_km"] = distance
            doctor_distances.append(doctor)

    doctor_distances.sort(key=lambda x: x["distance_km"])
    
    cursor.close()
    db.close()

    # check if the date is in the future
    today = datetime.today()
    correct_slots = []
    for doctor in doctor_distances:
        list_slots = doctor['available_slots'].split(', ')
        for slot in list_slots:
            if datetime.strptime(slot, '%Y-%m-%d %H:%M:%S') > today:
                correct_slots.append(slot)
        list_slots =", ".join(slot for slot in correct_slots)
        doctor['available_slots'] = list_slots
    
    return doctor_distances


checked_doctors = False
found_doctors=[]

def init_appointments_route(app):
    @app.route('/appointments', methods=['GET', 'POST'])
    def appointments_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in
        
        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
        
        specialty = session['specialty']
        global conversation # current conversation not previous
        doctors = find_doctors_by_criteria(specialty)
        # checks if user needs pwd accessible
        if session['need_pwd']:
            doctors = [doctor for doctor in doctors if doctor["pwd_accessible"] == 1]


        global checked_doctors
        if not checked_doctors:
            checked_doctors = True
            
            global found_doctors
            if doctors:
                    found_doctors.append({
                        "role": "assistant",
                        "content": f"I found {len(doctors)} {specialty}(s){' with pwd access' if session['need_pwd'] else ''} near you. Here are some options:"
                    })
            else:
                found_doctors.append({
                    "role": "assistant",
                    "content": f"Sorry, I couldn't find any {specialty}(s){' with pwd access' if session['need_pwd'] else ''} near you. Please try again later."
                })
                doctors = [{
                        "name": None,
                        "specialty": None,
                        "street": None,
                        "city": None,
                        "distance_km": 0,
                        "available_slots": None,
                        "pwd_accessible": None
                    }]


        if request.method == 'POST':
            #conversation = eval(request.form['conversation'])  # Convert string back to list
            user_message = request.form['user_message']

            response = agent_choose_book_appointment(conversation, user_message, doctors)
            conversation.append({"role": "user", "content": user_message})            
            conversation.append({"role": "assistant", "content": response})

        return render_template('appointments.html', conversation=conversation, doctors=doctors, found_doctors=found_doctors)  
