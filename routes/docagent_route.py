from flask import session, redirect, url_for, render_template, request
import json
from openai import OpenAI

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
        
        global conversation # Conversation history

        if request.method == 'POST':
            conversation = eval(request.form['conversation'])  # Convert string back to list
            user_message = request.form['user_message']

            conversation.append({"role": "doctor", "content": user_message})
        
        return render_template('docagent.html', conversation=conversation)