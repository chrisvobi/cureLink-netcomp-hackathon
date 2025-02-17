from flask import session, redirect, url_for, render_template, request
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from utils.db_connection import get_db_connection

def get_dates_in_range(start_day: str, end_day: str) -> list[str]:
    """Returns the dates between a start and end day"""
    
    today = datetime.today()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # calculate if the day is this week or next
    days_ahead = days_of_week.index(start_day) - today.weekday()
    days_ahead += 7 if days_ahead <= 0 else 0

    # starting day
    start_date = today + timedelta(days=days_ahead)

    days_ahead = days_of_week.index(end_day) - start_date.weekday()
    days_ahead += 7 if days_ahead <= 0 else 0


    # ending day
    end_date = start_date + timedelta(days=days_ahead)

    dates = []
    while start_date <= end_date:
        dates.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)

    return dates

def generate_times_in_range(start_time: str, end_time: str, interval: int) -> list[str]:
    """Returns the times between a start and end time"""
    # interval is minutes
    
    start_time = datetime.strptime(start_time, "%H:%M:%S")
    end_time = datetime.strptime(end_time, "%H:%M:%S")

    times = []
    while start_time <= end_time:
        times.append(start_time.strftime("%H:%M:%S"))
        start_time += timedelta(minutes=interval)

    return times

def generate_timedates(start_day: str, start_time: str, interval=60, end_day=None, end_time=None) -> list[str]:
    """Returns a list of timedates between a start and end day with a given interval and timespace"""
    timedates = []
    if end_day is None:
        today = datetime.today()
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_ahead = days_of_week.index(start_day) - today.weekday()
        days_ahead += 7 if days_ahead <= 0 else 0 
        date = today + timedelta(days=days_ahead)
        if end_time is None:
            start_time = datetime.strptime(start_time, "%H:%M:%S")
            timedates.append(f"{date.strftime('%Y-%m-%d')} {start_time.strftime('%H:%M:%S')}")
        else:
            times = generate_times_in_range(start_time, end_time, interval)
            for time in times:
                timedates.append(f"{date.strftime('%Y-%m-%d')} {time}")
    else:
        dates = get_dates_in_range(start_day, end_day)
        if end_time is None:
            start_time = datetime.strptime(start_time, "%H:%M:%S")
            for date in dates:
                timedates.append(f"{date} {start_time.strftime('%H:%M:%S')}")
        else:
            times = generate_times_in_range(start_time, end_time, interval)
            for date in dates:
                for time in times:
                    timedates.append(f"{date} {time}")
    return timedates


# insert slots into the database
def insert_slots(doctor_id: int, start_day: str, start_time: str, interval=60, end_day=None, end_time=None):
    db = get_db_connection("docagent_user")
    cursor = db.cursor(dictionary=True)
    # find latest slot date of the doctor

    dates = generate_timedates(start_day, start_time, interval, end_day, end_time)


    query = """
    SELECT max(slot_id) as maxslot, date_time FROM available_slots
    WHERE doctor_id = %s AND slot_id = (SELECT max(slot_id) FROM available_slots WHERE doctor_id = %s);
    """        
    cursor.execute(query, (doctor_id,doctor_id))
    row = cursor.fetchone()
    maxslot = row['maxslot'] if row['maxslot'] is not None else 0
    maxslot += 1
    date_time = str(row['date_time'])

    # only keep the dates that are greater than the latest date
    correct_dates = [date for date in dates if date > date_time]


    for date in correct_dates:
        query = """
        INSERT INTO available_slots (slot_id, doctor_id, date_time, booked)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (maxslot, doctor_id, date, 0))
        maxslot += 1

    db.commit()

    if len(correct_dates) > 0:
        return f"Successfully added {len(correct_dates)} slots as they were greater than your latest already added date"
    else:
        return "No slots were added as they were not greater than your latest added date"



with open('config.json') as config_file:
    config = json.load(config_file)
    key = config['KEY']

client = OpenAI(api_key=key)
model = 'gpt-4o-mini'

# System promts to initialize the agent
system_message = {
    "role": "system",
    "content": ( "You are a medical AI assistant designed to help a doctor."
        "Your goal is to help a doctor post their appointment schedule in a structured database. "
        "You ensure accurate data entry, prevent duplicate entries, validate appointment times, and format the data correctly."
        "Your responses should be clear, concise, and professional."
        "If you detect inconsistencies or potential errors, ask for clarification before proceeding."
    ),
}

# initialize the conversation with the system message
conversation = [system_message]

def init_docagent_route(app):
    @app.route('/docagent', methods=['GET', 'POST'])
    def docagent_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in
        
        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Redirect patients away
        
        global conversation # Conversation history

        if request.method == 'POST':
            conversation = eval(request.form['conversation'])  # Convert string back to list
            user_message = request.form['user_message']

            conversation.append({"role": "doctor", "content": user_message})
        
        return render_template('docagent.html', conversation=conversation)