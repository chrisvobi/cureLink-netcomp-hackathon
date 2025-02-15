import mysql.connector

try:
    db_connection = mysql.connector.connect(
        host="localhost",  
        user="root",
        password="12345678",
        database="med_db"
    )
    print("✅ Connected to MySQL successfully!")

    cursor = db_connection.cursor()
    cursor.execute("SELECT DATABASE();")
    print("Using database:", cursor.fetchone())

    cursor.execute("SHOW TABLES;")
    print("Tables:", cursor.fetchall())

    cursor.close()
    db_connection.close()

except mysql.connector.Error as err:
    print(f"❌ MySQL Connection Error: {err}")