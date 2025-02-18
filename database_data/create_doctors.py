from werkzeug.security import generate_password_hash
import mysql.connector
import random 
from datetime import datetime, timedelta

doc_names = [
    "Eva Georgakopoulou",
    "Stelios Zervos",
    "Ioannis Tsakalidis",
    "Anastasia Tsitsigka",
    "Petros Theodorakopoulos",
    "Eleni Papalexiou",
    "Spyros Karapetsas",
    "Katerina Tserepa",
    "Vassilios Zannis",
    "Irene Karachaliou",
    "Giorgos Papakostas",
    "Theofanis Roussos",
    "Marilena Kalaitzidou",
    "Kyriaki Lappas",
    "Aikaterini Vlahos",
    "Markos Papagiannis",
    "Stefanos Kotsis",
    "Dimitra Voulgaraki",
    "Nikolas Adamopoulos",
    "Anna Lymberopoulou",
    "Giorgos Nikolaidis",
    "Nikoleta Mavridou",
    "Thanasis Kriaras",
    "Haris Tsalouchidis",
    "Katerina Christodoulidou",
    "Alexandros Prassas",
    "Fotini Anastasopoulou",
    "Marios Economidis",
    "Rania Soulioti",
    "Spyridon Kleanthis",
    "Anastasia Manousaki",
    "Pavlos Loutrakiotis",
    "Vasiliki Dandoulaki",
    "Michalis Papazoglou",
    "Irene Georgiou",
    "Dionysios Kyriakidis",
    "Stella Papalexiou",
    "Alexandros Koutoupis",
    "Antigoni Meligkou",
    "Panagiotis Kourkoumelis",
    "Zoe Christodoulidou",
    "Giannis Nassiopoulos",
    "Marianna Papalexopoulou",
    "Markella Papanikolaou",
    "Andreas Drougou",
    "Kyriaki Kallivokas",
    "Nikos Markatos",
    "Leonidas Stratis",
    "Vasiliki Gavala",
    "Alexandros Nikolaidis",
    "Ioannis Papadopoulos",
    "Anastasia Papageorgiou",
    "Dimitrios Christodoulou",
    "Maria Vassilaki",
    "Konstantinos Katsaros",
    "Eleni Ioannou",
    "Nikolaos Koutras",
    "Sofia Georgiou",
    "Christos Antoniou",
    "Vasiliki Louka",
    "Giorgos Nikolaou",
    "Katerina Pavlou",
    "Panagiotis Daskalakis",
    "Ioanna Zervou",
    "Spyros Xatzistefanoglou",
    "Evangelia Pappa",
    "Pavlos Markopoulos",
    "Stamatia Iliadou",
    "Theodoros Zikos",
    "Andriana Stamatiou",
    "Aristeidis Katsiotis",
    "Dimitra Koutsou",
    "Alexandros Lamprou",
    "Konstantina Mylonas",
    "Michail Papageorgiou",
    "Eirini Chatzipavlou",
    "Theodoros Demetriou",
    "Fotini Drougou",
    "Antonios Leftheriotis",
    "Georgia Ioannidou",
    "Panayiotis Theodoridis",
    "Evangelos Papadopoulos",
    "Vasilis Papanikolaou",
    "Marilena Koutsou",
    "Charalambos Ioannou",
    "Alexandra Anastasopoulou",
    "Giorgos Athanasiou",
    "Maria Kyriakou",
    "Nikos Pavlidis",
    "Sotiros Christodoulou",
    "Rania Papoulia",
    "Lambros Kourtis",
    "Melina Sotiriou"
]

patient_names = [
    "Thanasis Kalogirou",
    "Foteini Kourou",
    "Kyriakos Georgiadis",
    "Marianna Tsiouma",
    "Dimitrios Konstantinidis",
    "Antonia Koutras",
    "Konstantinos Economou",
    "Aikaterini Lamprou",
    "Kostantinos Prassas",
    "Maria Aggelopoulou",
    "Kostantinos Skoularikis",
    "Grigorios Choutas",
    "Dimitrios Poulakis",
    "Ioannis Farfaras",
    "Ioannis Tranos",
    "Nikolas Papadopoulos",
    "Elias Konstantinou",
    "Dimitrios Georgiadis",
    "Christos Alexandrou",
    "Theodoros Vasilakis",
    "Antonis Markou",
    "Panagiotis Stefanidis",
    "Ioannis Kiriakou",
    "Spyros Zafeiris",
    "Athanasios Demetriou"
]

addresses_with_zip_codes = [
    ("Agiou Dimitriou 66", "54630"),
    ("Agiou Nikolaou 10", "54633"),
    ("Agiou Stylianou 5", "54642"),
    ("Agnostou Stratiotou 12", "54631"),
    ("Botsari Markou 15", "54643"),
    ("Deligianni Kanellou 20", "54641"),
    ("Egnatias 49", "54631"),
    ("Fleming Alexandrou 22", "54642"),
    ("Ionos Dragoumi 32", "54630"),
    ("Konstantinoupoleos 5", "54639"),
    ("Makedonikis Aminis 2", "54631"),
    ("Mitropolitou Gennadiou 8", "54631"),
    ("Orestou 14", "54642"),
    ("Psaron 3", "54642"),
    ("Solonos 6", "54642"),
    ("Stratigou Dousmani Viktoros 9", "54642"),
    ("Xenofontos 4", "54641"),
    ("Kolokotroni 24", "54641"),
    ("Doiranis 11", "54639"),
    ("Kilkisiou 8", "54639"),
    ("Litochorou 3", "54639"),
    ("Sarantaporou 15", "54640"),
    ("Miaouli 10", "54642"),
    ("Orestou 25", "54642"),
    ("Tompazi 10", "54644"),
    ("Nemeas 16", "54249"),
    ("Zarifi 5", "56123"),
    ("Kromnis 9", "54453"),
    ("Ikoniou 9", "54453"),
    ("Viziis 32", "54454"),
    ("Derkon 25", "54454"),
    ("Pafsania 25", "54352"),
    ("Semelis 24", "54352"),
    ("Vakchou 5", "54629"),
    ("Sapfous 19", "54627"),
    ("Sekeri 7", "54629"),
    ("Rousvelt 21", "56728"),
    ("Rousvelt 78", "56728"),
    ("Zaimi 25", "56625"),
    ("Klisthenous 17", "56625"),
    ("Filippou 18", "56625"),
    ("Pelopida 16", "54634"),
    ("Kassandrou 90", "54634"),
    ("Pelopos 5", "54633"),
    ("Moschonision 73", "55131"),
    ("Moschonision 65", "55131"),
    ("Sagariou 3", "55131"),
    ("Sagariou 5", "55131"),
    ("Taki Ikonomidi 53", "55131"),
    ("Chrisopigis 22", "55131"),
    ("Chrisopigis 7", "55131"),
    ("Xifilinon 4", "55131"),
    ("Xifilinon 23", "55131"),
    ("Nikopoleos 23", "55131"),
    ("Kromnis 6", "55131"),
    ("Trapezountos 59", "55131"),
    ("Nikopoleos 43", "55131"),
    ("Soumela 35", "55132"),
    ("Vazelonos 19", "55132"),
    ("Iasonidou 8", "55132"),
    ("Meotidos 14", "55133"),
    ("Kyzikou 10", "55133"),
    ("Diogenous 16", "55133"),
    ("Keramopoulou 2", "55133"),
    ("Kazaki 31", "55133"),
    ("Ikarou 4", "54250"),
    ("Dimocharous 12", "54250"),
    ("Antoniou Tousa 28", "54250"),
    ("Antisthenous 36", "54250"),
    ("Feakon 12", "54453"),
    ("Tinou 10", "54453"),
    ("Rodou 10", "54453"),
    ("Dorileou 34", "54454"),
    ("Dimitsanas 36", "54454"),
    ("Pileas 36", "54454"),
    ("Argeou 4", "54352"),
    ("Kapetan Ntrogra 8", "54352"),
    ("Mina Vista 24", "54352"),
    ("Mina Vista 4", "54352"),
    ("Semelis 13", "54352"),
    ("Pafsania 32", "54352"),
    ("Spirou Loui 32", "54352"),
    ("Spirou Loui 50", "54352"),
    ("Thermaikou 60", "54352"),
    ("Glinou 24", "54352"),
    ("Dimokritou 12", "54352"),
    ("Komninon 18", "56626"),
    ("Chortiati 2", "56626"),
    ("Ellis 4", "56626"),
    ("Megaron 9", "56626"),
    ("Makri 8", "56625"),
    ("Piston 7", "54632"),
    ("Mporou 5", "54632"),
    ("Manika 11", "56123"),
    ("Sokratous 14", "56123"),
    ("Idomenis 14", "56123"),
    ("Giannakopoulou 10", "56123"),
]

patient_addresses_with_zip_codes = [
    ("Ioulianou 8", "54635"),
    ("Kiprou 9", "56123"),
    ("Karaiskaki 12", "54641"),
    ("Kiprou 25", "54641"),
    ("Orestou 25", "54642"),
    ("Ionias 84", "54453"),
    ("Anteou 8", "54250"),
    ("Kiouptsidou 13", "55133"),
    ("Agiou Stefanou 3", "55132"),
    ("Dorileou 58", "54454"),
    ("Tideos 2", "54351"),
    ("Serron 13", "55337"),
    ("Simis 16", "54638"),
    ("Litochorou 8", "54639"),
    ("Chanion 4", "54639"),
    ("Parmenidou 10", "54352"),
    ("Megakleous 78", "54351"),
    ("Lisippou 4", "54351"),
    ("Kalavriton 30", "54351"),
    ("Igoumenou 20", "54634"),
    ("Argonafton 5", "54633"),
    ("Kessanis 68", "56728"),
    ("Alamanas 20", "56224"),
    ("Akropoleos 8", "56224"),
    ("Lasani 4", "56224"),
]

doctor_specialties = [
    "Allergist and Immunologist",
    "Cardiologist",
    "Dermatologist",
    "Endocrinologist",
    "Gastroenterologist",
    "General Practitioner"
    "Hematologist",
    "Hepatologist",
    "Infectious Disease",
    "Internist",
    "Nephrologist",
    "Neurologist",
    "Obstetrician",
    "Gynecologist",
    "Oncologist",
    "Ophthalmologist",
    "Optometrist",
    "Orthodontist",
    "Orthopedic Surgeon",
    "Otolaryngologist",
    "Pathologist",
    "Pediatrician",
    "Physiatrist",
    "Plastic Surgeon",
    "Psychiatrist",
    "Pulmonologist",
    "Radiologist",
    "Rheumatologist",
    "Sleep Medicine Specialist",
    "Sports Medicine Physician",
    "Toxicologist",
    "Urologist"
]

most_common_conditions = [
    "Hypertension",
    "Diabetes",
    "Asthma",
    "Heart Disease",
    "Stroke",
    "Arthritis",
    "Obesity",
    "Osteoporosis",
    "Alzheimer's Disease",
    "Cancer",
    "Gastroesophageal Reflux Disease",
    "Chronic Kidney Disease"
]

def create_email(name):
    a = name.split(" ")  
    email = a[0].lower() + "." + a[1].lower() + "@email.com"  
    return email

def create_password(name, zip_code):
    a = name.split(" ")
    password = a[0].lower() + a[1].lower()[0:3] + zip_code[-2:]
    hashed_password = generate_password_hash(password, method='pbkdf2:sha512')
    return password, hashed_password

def add_addresses():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123tasaras321",
        database="med_db"
    )
    cursor = db.cursor()

    # Extract distinct zip codes
    unique_zip_codes = sorted(set(zip_code for _, zip_code in patient_addresses_with_zip_codes))
    print(unique_zip_codes)
    # SQL Insert Query
    insert_query = """
    INSERT INTO address (zip_code, city) VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE city = VALUES(city);
    """

    # Insert each unique zip code into the table
    for zip_code in unique_zip_codes:
        cursor.execute(insert_query, (zip_code, "Thessaloniki"))

    # Commit changes and close connection
    db.commit()
    cursor.close()
    db.close()

    print("Distinct zip codes added to the address table successfully!")

def add_doctors():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123tasaras321",
        database="med_db"
    )
    
    cursor = db.cursor()

    insert_query = """
    INSERT INTO doctors (doctor_id, name, email, password, specialty, zip_code, street, pwd_accessible) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    doctor_id = 1  # Start doctor_id counter

    for specialty in doctor_specialties:
        for _ in range(3):  # Add 3 doctors per specialty
            name = doc_names[doctor_id-1]
            address, zip_code = addresses_with_zip_codes[doctor_id-1]  # Pick a random address
            email = create_email(name)
            password, password_hashed = create_password(name, zip_code)
            pwd_accessible = random.choice([0, 1, 1])

            cursor.execute(insert_query, (doctor_id, name, email, password_hashed, specialty, zip_code, address, pwd_accessible))
            doctor_id += 1  # Increment doctor_id

    db.commit()
    cursor.close()
    db.close()

    print("Doctors inserted successfully into MySQL database!")

def add_patients():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123tasaras321",
        database="med_db"
    )
    
    cursor = db.cursor()

    insert_query = """
    INSERT INTO patients (patient_id, name, email, password, zip_code, street, age, gender, medical_record, family_history) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for i in range(len(patient_names)):  
        name = patient_names[i]
        email = create_email(name)
        address, zip_code = patient_addresses_with_zip_codes[i]
        password, password_hashed = create_password(name, zip_code)
        age = random.randint(18, 80)  
        gender = "male"  # FIX MANUALLY
        medical_record_count = random.choice([0, 1])
        medical_record = ", ".join(random.sample(most_common_conditions, medical_record_count)) if medical_record_count > 0 else None
        family_history_count = random.choice([0, 1, 1, 2])
        family_history = ", ".join(random.sample(most_common_conditions, family_history_count)) if family_history_count > 0 else None


        cursor.execute(insert_query, (i+1, name, email, password_hashed, zip_code, address, age, gender, medical_record, family_history))

    db.commit()
    cursor.close()
    db.close()

    print("Patients inserted successfully into MySQL database!")

def add_available_slots():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123tasaras321",
        database="med_db"
    )
    cursor = db.cursor()

    doctor_ids = [i for i in range(1, 94)]  # Assuming 5 doctors

    # Define the specific dates and time slots
    specific_dates = [
        datetime(2025, 2, 13),
        datetime(2025, 2, 14),
        datetime(2025, 2, 24),
        datetime(2025, 2, 25),
        datetime(2025, 2, 26),
    ]
    time_slots = ["10:00:00", "11:00:00", "12:00:00", "13:00:00", "14:00:00", "15:00:00", "16:00:00"]

    # SQL Insert Query
    insert_query = """
    INSERT INTO available_slots (slot_id, doctor_id, date_time, booked) 
    VALUES (%s, %s, %s, %s)
    """

    # Generate and insert slots for each doctor
    

    for doctor_id in doctor_ids:
        slot_id = 1  # Global slot ID counter
        for current_date in specific_dates:
            for time in time_slots:
                date_time = f"{current_date.strftime('%Y-%m-%d')} {time}"
                cursor.execute(insert_query, (slot_id, doctor_id, date_time, 0))
                slot_id += 1  # Increment slot_id globally

    # Commit changes and close connection
    db.commit()
    cursor.close()
    db.close()

    print("Time slots inserted successfully into MySQL database!")

def add_appointments():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123tasaras321",
        database="med_db"
    )
    cursor = db.cursor()

    # Get the list of patient IDs
    patient_ids = [i for i in range(1, 26)]  # Assuming 15 patients
    random.shuffle(patient_ids)  # Shuffle to distribute fairly

    # SQL Insert Query for appointments
    insert_query = """
    INSERT INTO appointments (patient_id, doctor_id, slot_id, status, diagnosis, medicine) 
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    # SQL Update Query for available_slots (marks as booked)
    update_query = "UPDATE available_slots SET booked = 1 WHERE slot_id = %s AND doctor_id = %s;"

    current_time = datetime.now()

    # Sample medical conditions and medicines
    diagnoses = ["Healthy"]
    medicines = [None]

    # Loop through each patient
    for patient_id in patient_ids:
        assigned_slots = set()  # Store assigned slot_ids for this patient to avoid duplicate slots

        # Fetch all doctor IDs dynamically
        cursor.execute("SELECT DISTINCT doctor_id FROM available_slots WHERE booked = 0;")
        doctor_ids = [row[0] for row in cursor.fetchall()]
        print(len(doctor_ids))
        random.shuffle(doctor_ids)
        print(len(doctor_ids))

        for doctor_id in doctor_ids:
            # Fetch updated available slots for this doctor
            cursor.execute(
                "SELECT slot_id, date_time FROM available_slots WHERE doctor_id = %s AND booked = 0;",
                (doctor_id,)
            )
            slots = cursor.fetchall()  # [(slot_id, date_time), ...]

            if not slots:
                continue  # Skip if no slots are available for this doctor

            # Select a random slot that hasn't been assigned yet
            available_slots = [slot for slot in slots if slot[0] not in assigned_slots]
            if not available_slots:
                continue

            slot_id, date_time = random.choice(available_slots)
            assigned_slots.add(slot_id)  # Mark this slot as assigned

            # Convert date_time string to a datetime object
            slot_datetime = datetime.strptime(str(date_time), "%Y-%m-%d %H:%M:%S")

            # Determine appointment status
            if slot_datetime < current_time:
                status = "completed"
                diagnosis = random.choice(diagnoses)
                medicine = random.choice(medicines)
            else:
                status = "scheduled"
                diagnosis = None
                medicine = None

            # Insert into appointments table
            cursor.execute(insert_query, (patient_id, doctor_id, slot_id, status, diagnosis, medicine))

            # Update available_slots table to set booked = 1
            cursor.execute(update_query, (slot_id, doctor_id))

    # Commit changes and close connection
    db.commit()
    cursor.close()
    db.close()

    print("Appointments inserted successfully! Each patient has one appointment with each doctor at a random slot.")

def patients_accounts(filename="patient_accounts.txt"):
    """Generate patient accounts and save them in an aligned format."""
    with open(filename, "w") as file:
        max_email_length = max(len(create_email(name)) for name in patient_names)  # Find longest email

        for i in range(len(patient_names)):  
            name = patient_names[i]
            email = create_email(name)
            address, zip_code = patient_addresses_with_zip_codes[i]
            password, hashed_password = create_password(name, zip_code)

            # Writing formatted output to file
            file.write(f"{email.ljust(max_email_length + 10)}  {password}\n")

    print(f"Patient accounts saved to {filename}")

def doctors_accounts(filename="doctor_accounts.txt"):
    """Generate doctor accounts and save them in an aligned format."""
    with open(filename, "w") as file:
        max_email_length = max(len(create_email(name)) for name in doc_names)  # Find longest email

        for i in range(len(doc_names)):  
            name = doc_names[i]
            email = create_email(name)
            address, zip_code = addresses_with_zip_codes[i]
            password, hashed_password = create_password(name, zip_code)

            # Writing formatted output to file
            file.write(f"{email.ljust(max_email_length + 10)}  {password}\n")

    print(f"Doctor accounts saved to {filename}")
            

# add_addresses()
# add_doctors()
# add_patients()
# add_available_slots()
# add_appointments()

# patients_accounts()
# doctors_accounts()