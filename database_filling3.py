import mysql.connector
import random
from datetime import datetime

try:
    # Step 1: Connect to MySQL database
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="med_db"
    )
    print("✅ Connected to MySQL successfully!")

    cursor = db_connection.cursor()

    # Define a list of possible past medical conditions
    past_medical_conditions = [
        "Hypertension",
        "Diabetes",
        "Asthma",
        "Chronic Bronchitis",
        "Heart Disease",
        "Kidney Failure",
        "Cancer Survivor",
        "Osteoporosis",
        "Allergies to Penicillin",
        "Thyroid Disease",
        "Previous Stroke",
        "High Cholesterol",
        "Arthritis",
        "HIV/AIDS",
        "Lung Disease"
    ]

    # Define a list of family history options
    family_history_options = [
        "No known family history",
        "Family history of hypertension",
        "Family history of diabetes",
        "Family history of heart disease",
        "Family history of cancer",
        "Family history of stroke"
    ]

    # Step 2: Fill in the new attributes (age, gender, medical_record, family_history) for the patients
    for patient_id in range(1, 43):  # Patient IDs from 1 to 42
        # Generate a random age between 18 and 80
        age = random.randint(18, 80)

        # Randomly assign gender (female or male)
        gender = random.choice(['female', 'male'])

        # Select one or two random past medical conditions to form the medical record
        medical_record = ', '.join(random.sample(past_medical_conditions, random.randint(1, 2)))

        # Generate a random family history description
        family_history = random.choice(family_history_options)

        # Step 3: Update the patient record with the generated values
        cursor.execute('''
            UPDATE patients
            SET age = %s, gender = %s, medical_record = %s, family_history = %s
            WHERE patient_id = %s;
        ''', (age, gender, medical_record, family_history, patient_id))

        print(f"Updated patient {patient_id}: Age {age}, Gender {gender}, Medical Record {medical_record}, Family History {family_history}.")

    # Step 4: Commit the changes to the database
    db_connection.commit()

    # Step 5: Close the cursor and the database connection
    cursor.close()
    db_connection.close()
    print("✅ MySQL connection closed.")

except mysql.connector.Error as err:
    print(f"❌ MySQL Error: {err}")
