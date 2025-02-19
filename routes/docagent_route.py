from flask import session, redirect, url_for, render_template, request
import json
from openai import OpenAI
from datetime import datetime, timedelta
from utils.db_connection import get_db_connection

def insert_slots_multiple_days(doctor_id: int, start_day: list[str], start_time: str, interval=60,end_day=None, end_time=None):
    """Handles inserting slots for multiple days, supporting both weekdays and specific dates."""
    results = []  # To store the results if needed
    for day in start_day:
        result = insert_slots(doctor_id, day, start_time, interval, end_day, end_time)  # Call insert_slots for each day
        results.append(result)  # Collect each result 
    total_slots = 0
    for res in results:
        if "Successfully added" in res:
            total_slots += int(res.split()[2])
    if total_slots > 0:
        return f"Successfully added {total_slots} slots as these were available in your schedule."
    else:
        return "No slots were added as you already have slots for these dates"

def insert_slots_multiple_days_second(doctor_id: int, start_day: list[str], start_time: str, interval=60,end_day=None, end_time=None):
    """Handles inserting slots for multiple days, supporting both weekdays and specific dates."""

    results = []  # To store the results if needed
    for day in start_day:
        result = insert_slots2(doctor_id, day, start_time, interval, end_day, end_time)  # Call insert_slots for each day
        results.append(result)  # Collect each result
        
    total_slots = 0
    for res in results:
        if "Successfully added" in res:
            total_slots += int(res.split()[2])
    if total_slots > 0:
        return f"Successfully added {total_slots} slots as these were available in your schedule."
    else:
        return "No slots were added as you already have slots for these dates"

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
    SELECT max(slot_id) as maxslot FROM available_slots
    WHERE doctor_id = %s;
    """        
    cursor.execute(query, (doctor_id,))
    row = cursor.fetchone()
    maxslot = row['maxslot'] if row['maxslot'] is not None else 0
    maxslot += 1

    query = """
    SELECT date_time FROM available_slots
    WHERE doctor_id = %s
    """
    cursor.execute(query, (doctor_id,))
    date_times = cursor.fetchall()
    date_times = [str(date_times[i]['date_time']) for i in range(len(date_times))]

    # only keep the dates that are greater than the latest date
    correct_dates = [date for date in dates if date not in date_times]


    for date in correct_dates:
        query = """
        INSERT INTO available_slots (slot_id, doctor_id, date_time, booked)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (maxslot, doctor_id, date, 0))
        maxslot += 1

    db.commit()

    if len(correct_dates) > 0:
        return f"Successfully added {len(correct_dates)} slots as these were available in your schedule."
    else:
        return "No slots were added as you already have slots for these dates"

def insert_slots2(doctor_id: int, start_day: str, start_time: str, interval=60, end_day=None, end_time=None):
    db = get_db_connection("docagent_user")
    cursor = db.cursor(dictionary=True)
    end_day = end_day if end_day is not None else start_day
    dates = []
    
    # Convert days to datetime objects
    start_day = datetime.strptime(start_day, "%Y-%m-%d")
    end_day = datetime.strptime(end_day, "%Y-%m-%d")
    
    # Generate the list of dates between start and end day
    while start_day <= end_day:
        dates.append(start_day.strftime("%Y-%m-%d"))
        start_day += timedelta(days=1)
        
    timedates = []
    
    # If end_time is None, only append the start time
    if end_time is None:
        start_time = datetime.strptime(start_time, "%H:%M:%S")
        for date in dates:
            timedates.append(f"{date} {start_time.strftime('%H:%M:%S')}")
    else:
        # Otherwise, generate times between start_time and end_time at the specified interval
        times = generate_times_in_range(start_time, end_time, interval)
        for date in dates:
            for time in times:
                timedates.append(f"{date} {time}")
    
    # Query to get the max slot_id in the available_slots table for this doctor
    query = """
    SELECT max(slot_id) as maxslot FROM available_slots
    WHERE doctor_id = %s
    """        
    cursor.execute(query, (doctor_id,))
    row = cursor.fetchone()
    maxslot = row['maxslot'] if row['maxslot'] is not None else 0
    maxslot += 1

    # Query to get all existing date_times from the available_slots table
    query = """
    SELECT date_time FROM available_slots
    WHERE doctor_id = %s
    """
    cursor.execute(query, (doctor_id,))
    date_times = cursor.fetchall()
    date_times = [str(date_times[i]['date_time']) for i in range(len(date_times))]


    # only keep the dates that are in the future and not already in the database
    today = datetime.today()
    correct_dates = []

    for date in timedates:
        if date not in date_times:
            if datetime.strptime(date, '%Y-%m-%d %H:%M:%S') > today:
                correct_dates.append(date)

    
    for date in correct_dates:
        query = """
        INSERT INTO available_slots (slot_id, doctor_id, date_time, booked)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (maxslot, doctor_id, date, 0))
        maxslot += 1

    db.commit()

    # Return a message depending on how many slots were added
    if len(correct_dates) > 0:
        return f"Successfully added {len(correct_dates)} slots as these were available in your schedule."
    else:
        return "No slots were added as you already have slots for these dates or they are in the past."

def create_appointments(conversation, user_message):
    """openai model to create appointments"""
    completion = client.chat.completions.create(
    model=model,
    messages=conversation + [{"role": "user", "content": user_message}],
    functions=function_descriptions,
    function_call="auto",
    )
    # take params from the function call
    output = completion.choices[0].message
    if output.function_call is None:
        return output.content
    params = json.loads(output.function_call.arguments)
    # default values if the user didnt give them
    interval = params["interval"] if "interval" in params else 60
    end_day = params["end_day"] if "end_day" in params else None
    end_time = params["end_time"] if "end_time" in params else None
    # arguments for the insert_slots function
    args = {
    "doctor_id": session['user_id'],
    "start_day": params["start_day"],
    "start_time": params["start_time"],
    "interval": interval,
    "end_day": end_day,
    "end_time": end_time,
    }
    fun = output.function_call.name
    call = call_function(fun, args)
    return call

def call_function(name, args):
    if name == "insert_slots":
        return insert_slots(**args)
    elif name == "insert_slots2":
        return insert_slots2(**args)
    elif name == "insert_slots_multiple_days":
        return insert_slots_multiple_days(**args)
    elif name == "insert_slots_multiple_days_second":
        return insert_slots_multiple_days_second(**args)


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
        "Interval, end_day, and end_time are optional parameters."
        "Don't ask for clarifications if the parameters are optional"
        f"today's date is {datetime.today().strftime('%Y-%m-%d')}"
        "if the year is not provided, assume it is the current year"
        "if the month is not provided, assume it is the current month"
        "don't ask for confirmation in your assumptions"
        "if user says something irrelevant remind them your purpose"
        "if user gives a day (eg Monday) of the week call function insert_slots"
        "if user gives a date (%y-%m-%d) call function insert_slots2"
        "never assume end_day and end_time if they are not provided"
        "if a day is given one time end day is None"
        "if a time is given one time end time is None"
        "if user gives multiple days (eg Monday , Wednesday and Friday) set start day as list of these days and set end day as None"
        "if user gives multiple days (eg Monday , Wednesday and Friday) call function insert_slots_multiple_days"
        "if user gives multiple dates (eg 2025/02/19 , 2025/02/21 and 2025/02/23) call function insert_slots_multiple_days_second"
    ),
}

# initialize the conversation with the system message
conversation = [system_message]

function_descriptions = [
    {
        "name": "insert_slots",
        "description": "Insert an available slot for appointments into the database",
        "parameters": {
            "type": "object",
            "properties": {
                "start_day": {
                    "type": "string",
                    "description": "The first day of the available slots, e.g. Monday",
                },
                "start_time": {
                    "type": "string",
                    "description": "The start time of the available slots, e.g. 09:00:00",
                },
                "interval": {
                    "type": "integer",
                    "description": "The interval in minutes between each slot, e.g. 60",
                },
                "end_day": {
                    "type": "string",
                    "description": "The last day of the available slots, e.g. Friday",
                },
                "end_time": {
                    "type": "string",
                    "description": "The end time of the available slots, e.g. 17:00:00",
                },
            },
            "required": ["start_day", "start_time"],
        },
    },
    {
        "name": "insert_slots2",
        "description": "Insert an available slot for appointments into the database",
        "parameters": {
            "type": "object",
            "properties": {
                "start_day": {
                    "type": "string",
                    "description": "The first date of the available slots in the format YYYY-MM-DD",
                },
                "start_time": {
                    "type": "string",
                    "description": "The start time of the available slots, e.g. 09:00:00",
                },
                "interval": {
                    "type": "integer",
                    "description": "The interval in minutes between each slot, e.g. 60",
                },
                "end_day": {
                    "type": "string",
                    "description": "The last date of the available slots in the format YYYY-MM-DD",
                },
                "end_time": {
                    "type": "string",
                    "description": "The end time of the available slots, e.g. 17:00:00",
                },
            },
            "required": ["start_day", "start_time"],
        },
    },
     {
        "name": "insert_slots_multiple_days",
        "description": "Insert available slots for appointments for multiple days into the database",
        "parameters": {
            "type": "object",
            "properties": {
                "start_day": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "A list of days as strings. Each can be a weekday (e.g., 'Monday')."
                    },
                    "description": "A list of days for which to insert available slots."
                },
                "start_time": {
                    "type": "string",
                    "description": "The start time of the available slots, in the format HH:MM:SS (e.g., '09:00:00')."
                },
                "interval": {
                    "type": "integer",
                    "description": "The interval in minutes between each slot, e.g., 60. Default is 60."
                },
                "end_time": {
                    "type": "string",
                    "description": "The end time for the slots in the format HH:MM:SS (e.g., '17:00:00'). Optional."
                }
            },
            "required": [ "start_day", "start_time"]
        }
    },
    {
        "name": "insert_slots_multiple_days_second",
        "description": "Insert available slots for appointments for multiple days into the database",
        "parameters": {
            "type": "object",
            "properties": {
                "start_day": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "A list of days as strings. Each can be a date (YYYY-MM-DD)."
                    },
                    "description": "A list of days for which to insert available slots."
                },
                "start_time": {
                    "type": "string",
                    "description": "The start time of the available slots, in the format HH:MM:SS (e.g., '09:00:00')."
                },
                "interval": {
                    "type": "integer",
                    "description": "The interval in minutes between each slot, e.g., 60. Default is 60."
                },
                "end_time": {
                    "type": "string",
                    "description": "The end time for the slots in the format HH:MM:SS (e.g., '17:00:00'). Optional."
                }
            },
            "required": [ "start_day", "start_time"]
        }
    }
]
chat = [system_message]
def init_docagent_route(app):
    @app.before_request
    def before_request():
        if request.method == 'GET' and request.endpoint == 'docagent_page' and not request.args:
            global conversation, chat
            conversation = [system_message]
            chat = conversation
    
    @app.route('/docagent', methods=['GET', 'POST'])
    def docagent_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in

        if session.get('user_type') != "doctor":  
            return redirect(url_for('login'))  # Redirect patients away
        
        global conversation # current conversation

        if request.method == 'POST':
            conversation = eval(request.form['conversation'])  # Convert string back to list
            user_message = request.form['user_message']

            response = create_appointments(conversation, user_message)
            if "No slots were added" or "Successfully added" in response:
                conversation = [system_message]
            else:
                conversation.append({"role": "user", "content": user_message})
                conversation.append({"role": "assistant", "content": response})
            chat.append({"role": "user", "content": user_message})
            chat.append({"role": "assistant", "content": response})
        
        return render_template('docagent.html', conversation=chat)