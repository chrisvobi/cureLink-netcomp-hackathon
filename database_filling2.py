import mysql.connector
import random
from datetime import datetime, timedelta

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

    # Step 2: Define the target dates for scheduling, canceling, and completing
    target_dates = [
        datetime(2025, 2, 23),
        datetime(2025, 2, 24),
        datetime(2025, 2, 25),
        datetime(2025, 2, 17)  # We will also process Feb 17 separately for "completed"
    ]

    # Define the specific times you want for each date
    times = ["09:00:00", "10:00:00", "11:00:00"]

    # Create the final list of datetime objects with the specific times
    date_time_list = [
        datetime.combine(date, datetime.min.time()) + timedelta(hours=int(time.split(':')[0]), minutes=int(time.split(':')[1]), seconds=int(time.split(':')[2]))
        for date in target_dates
        for time in times
    ]

    # Step 3: Process appointments for dates Feb 23, 24, and 25 (scheduled or canceled)
    for target_date in date_time_list:  # Processing the first 3 dates (Feb 23, 24, 25)
        for _ in range(10):  # Making 10 random appointments as an example for each date
            # Randomly select a patient_id (from 1 to 42)
            patient_id = random.randint(1, 42)

            # Randomly select a doctor_id (from 1 to 40)
            doctor_id = random.randint(1, 40)

            # Randomly select a slot_id (4 to 12) for this doctor (for Feb 23, 24, 25)
            slot_id = random.randint(4, 12)

            # Fetch the available slot for the target date
            cursor.execute(''' 
            SELECT slot_id, date_time FROM available_slots 
            WHERE doctor_id = %s AND slot_id = %s AND booked = 0 AND DATE(date_time) = %s LIMIT 1;
            ''', (doctor_id, slot_id, target_date.date()))

            available_slot = cursor.fetchone()

            if available_slot:
                # If a slot is available, randomly decide if the appointment will be 'scheduled' or 'canceled'
                status = random.choice(['scheduled', 'canceled'])  # Randomly choose the status

                slot_id, slot_time = available_slot
                cursor.execute(''' 
                INSERT INTO appointments (patient_id, doctor_id, slot_id, status) 
                VALUES (%s, %s, %s, %s);
                ''', (patient_id, doctor_id, slot_id, status))

                print(f"Appointment for patient {patient_id} with doctor {doctor_id} at {slot_time}, Slot {slot_id}, Status {status}.")

            else:
                print(f"No available slot for doctor {doctor_id}, slot {slot_id} on {target_date.date()}.")

    # Step 4: Process appointments for February 17, 2025 (mark as 'completed')
    for _ in range(10):  # Processing 10 appointments on Feb 17, 2025
        # Randomly select a patient_id (from 1 to 42)
        patient_id = random.randint(1, 42)

        # Randomly select a doctor_id (from 1 to 40)
        doctor_id = random.randint(1, 40)

        # Randomly select a slot_id (1 to 3) for this doctor (for Feb 17)
        slot_id = random.randint(1, 3)

        # Fetch the already booked slot for February 17, 2025
        cursor.execute(''' 
        SELECT slot_id, date_time FROM available_slots 
        WHERE doctor_id = %s AND slot_id = %s AND booked = 0 AND DATE(date_time) = %s LIMIT 1;
        ''', (doctor_id, slot_id, datetime(2025, 2, 17).date()))

        available_slot = cursor.fetchone()

        if available_slot:
            # First, mark the slot as booked (booked = 1)
            slot_id, slot_time = available_slot
            cursor.execute(''' 
            UPDATE available_slots
            SET booked = 1
            WHERE doctor_id = %s AND slot_id = %s AND date_time = %s;
            ''', (doctor_id, slot_id, slot_time))
            db_connection.commit()

            # Now, mark the appointment as 'completed'
            cursor.execute(''' 
            INSERT INTO appointments (patient_id, doctor_id, slot_id, status) 
            VALUES (%s, %s, %s, 'completed');
            ''', (patient_id, doctor_id, slot_id))

            print(f"Appointment for patient {patient_id} with doctor {doctor_id} at {slot_time}, Slot {slot_id} marked as 'completed'.")
        
        else:
            print(f"No available slot for doctor {doctor_id}, slot {slot_id} on February 17, 2025.")

    # Step 5: Commit the changes to the database
    db_connection.commit()

    # Step 6: Close the cursor and the database connection
    cursor.close()
    db_connection.close()
    print("✅ MySQL connection closed.")

except mysql.connector.Error as err:
    print(f"❌ MySQL Error: {err}")
