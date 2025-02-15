from flask import render_template, request, session, redirect, url_for
import mysql.connector
import json



def get_db_connection(user_type="app_user"):
    # Load DB configuration
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    """Returns a database connection based on the user type."""
    db_user = config[user_type]
    return mysql.connector.connect(
        host=config["host"],
        user=db_user["user"],
        password=db_user["password"],
        database=config["database"]
    )

def init_main_route(app):
    @app.route('/main', methods=['GET', 'POST'])
    def main_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in
        
        user_id = session['user_id']  # Retrieve user ID

        # Connect with `app_user`
        db = get_db_connection("app_user")
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (user_id,))
        user_data = cursor.fetchall()
        cursor.close()
        db.close()

        return render_template('main.html', user_id=user_id, user_data=user_data)
