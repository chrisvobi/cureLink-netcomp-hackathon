import mysql.connector
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

    # Step 2: Define the start time, duration, and slots per doctor
    start_time = datetime(2025, 2, 25, 9, 0)  # Starting at 09:00 AM on February 17, 2025
    slot_duration = timedelta(hours=1)  # 1-hour interval between slots

    # Step 3: Loop for doctor_id from 1 to 40
    for doctor_id in range(1, 41):  # doctor_id from 1 to 40 (inclusive)
        # Loop for each slot_id (1 to 3)
        for slot_id in range(12, 16):  # slot_id from 1 to 3
            # Calculate the slot's date_time (e.g., 09:00, 10:00, 11:00 for each doctor)
            slot_time = start_time + (slot_id - 1) * slot_duration  # Calculate time for each slot
            cursor.execute('''
            INSERT INTO available_slots (doctor_id, slot_id, date_time, booked) 
            VALUES (%s, %s, %s, %s)''', (doctor_id, slot_id, slot_time, 0))  # Booked = 0 (available)
            print(f"Inserted slot for doctor {doctor_id}, slot {slot_id} at {slot_time}")

    # Step 4: Commit the changes to the database
    db_connection.commit()

    # Step 5: Verify the inserted data by fetching all records
    cursor.execute('SELECT * FROM available_slots')
    rows = cursor.fetchall()

    # Print the result
    for row in rows:
        print(row)

    # Step 6: Close the cursor and the database connection
    cursor.close()
    db_connection.close()
    print("✅ MySQL connection closed.")

except mysql.connector.Error as err:
    print(f"❌ MySQL Error: {err}")
