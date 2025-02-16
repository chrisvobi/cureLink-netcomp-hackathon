from flask import render_template, session
import math
import requests
import json
from utils.db_connection import get_db_connection 


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
        SELECT city , zip_code
        FROM address 
        WHERE address.zip_code = %s
    """, (session['zip_code'],))
    patient_data = cursor.fetchone()

    patient_address = f"{session['street']} { patient_data['city']} {patient_data['zip_code']}"
    patient_city =  patient_data['city']
    patient_lat, patient_lon = get_coordinates(patient_address)
    query = """
    SELECT d.doctor_id, d.name, d.specialty, d.zip_code, d.street, addr.city,
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

    return doctor_distances

    

def init_appointments_route(app):
    @app.route('/appointments')
    def appointments_page():
        specialty = session['specialty']
        conversation = session['conversation']
        doctors = find_doctors_by_criteria(specialty)
        if doctors:
                conversation.append({
                    "role": "assistant",
                    "content": f"I found {len(doctors)} {specialty}(s) near you. Here are some options:"
                })
        else:
            conversation.append({
                "role": "assistant",
                "content": f"Sorry, I couldn't find any {specialty}(s) near you. Please try again later."
            })
            doctors = [{
                    "name": None,
                    "specialty": None,
                    "street": None,
                    "city": None,
                    "distance_km": 0,
                    "available_slots": None
                }]

        return render_template('appointments.html', conversation=conversation[-1], doctors=doctors)  
