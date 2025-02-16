import json
import mysql.connector
from flask import flash

def get_db_connection(user_type):
    # Load DB secrets
    with open('db.json', 'r') as config_file:
        config = json.load(config_file)

    # Returns a database connection based on the user type
    db_user = config[user_type]
    if not db_user:
            flash(f"Database user type '{user_type}' not found in config.", "danger")
            return None 
    
    # Connects as user type
    db = mysql.connector.connect(
        host=config["host"],
        user=db_user["user"],
        password=db_user["password"],
        database=config["database"]
    )
    
    if db is None:
        flash("Database connection failed!", "danger")
        return None

    return db