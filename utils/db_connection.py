import json
import mysql.connector
from flask import flash

def get_db_connection(user_type):
    # Load database credentials from db.json
    with open('db.json', 'r') as config_file:
        config = json.load(config_file)

    # Retrieve user credentials for the specified user type
    db_user = config.get(user_type)
    if not db_user:
        flash(f"Database user type '{user_type}' not found in config.", "danger")
        return None 
    
    # Establish a connection to the MySQL database
    db = mysql.connector.connect(
        host=config["host"],
        user=db_user["user"],
        password=db_user["password"],
        database=config["database"]
    )
    
    # Check if the connection failed
    if db is None:
        flash("Database connection failed!", "danger")
        return None

    return db