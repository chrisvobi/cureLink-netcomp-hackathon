from openai import OpenAI
from pydantic import BaseModel, Field
import json
from difflib import get_close_matches
from utils.db_connection import get_db_connection
from flask import render_template, request, session, redirect, url_for
from utils.db_connection import get_db_connection


# Load openai API key initialize model
with open('config.json') as config_file:
    config = json.load(config_file)
    key = config['KEY']
client = OpenAI(api_key=key)
model = 'gpt-4o-mini'

# System message
system_message = {
    "role": "system",
    "content": (
        "You are a medical AI assistant. Your goal is to ask relevant follow-up questions "
        "before making a diagnosis or recommending a specialist. "
        "Only recommend a specialist when you are at least 90% confident. "
        "recommend only ONE specialist"
        "your answer about a specialist should be 1-2 words at max, ideally just one"
        "If unsure, keep asking questions to gather more information. "
        "Never make bold assumptions or provide a diagnosis too early."
        "If you are at least 90% confident that the symptoms are not severe, and you have ruled out that the patient needs a doctor, recommend simple at-home treatment."
        "If you are sure that the user isn't describing symptoms and requested for a doctor, reccomend and appointment"
    ),
}
added_history = False # Boolean to check if the patient history has been given to the agent
conversation = [system_message]

# Use BaseModel to extract diagnosis and doctor specialty (with confidence score) from the users symptoms
class DoctorExtraction(BaseModel):
    diagnosis: str = Field(description="Possible diagnosis based on the user's symptoms")
    specialty: str = Field(description="Relevant doctor's specialty (e.g., 'Cardiologist')")
    confidence_score: float = Field(description="Confidence score (0-1) for recommending a doctor")

# Use BaseModel to check if the users symptoms require urgent care (with confidence score)
class UrgentAttention(BaseModel):
    is_urgent: bool = Field(description="True if the symptoms require immediate emergency attention, False otherwise")
    confidence_score: float = Field(description="Confidence score (0-1) for classifying symtoms as urgent")
    reason: str = Field(description="Brief reason why emergency attention is necessary")

# Use BaseModel to check if the users symptoms are not severe (with confidence score)
class SymptomsNotSevere(BaseModel):
    at_home_treatment: str = Field(description="Recommendation for at-home treatment, based on symptoms")
    confidence_score: float = Field(description="Confidence score (0-1) for recommending at-home treatment")

# Use BaseModel to get next question to ask the user
class Questions(BaseModel):
    question: str = Field(description="The question to ask the user")

# Use BaseModel to check if the user response is relevant
class InputValidation(BaseModel):
    is_relevant: bool = Field(description="Indicates whether the user's input is medically relevant")

# Use BaseModel to extract doctor specialty (with confidence score) when the user requests directly a doctor
class RequestDoctor(BaseModel):
    specialty: str = Field(description="Relevant doctor's specialty (e.g., 'Cardiologist') that the user requested")
    confidence_score: float = Field(description="Confidence score (0-1) that the user requested a specific doctor")

# Use BaseModel to extract if the user has a disability
class DisabledAccess(BaseModel):
    is_disabled: bool = Field(description="True if the user has a disability and needs pwd (people with disabilities) access, False otherwise")

relevance_check ={
    "role": "system",
    "content": ("You are a medical assisant that classifies whether a given input is medically relevant."
    "User input should contain health related or medical terms."
    "if the user input is yes or no it probably is related to questions about symptoms or conditions."
    "keep in mind that the user might not be aware of the medical terms, so try to understand the context of the message.")
}
# Function to check if user input is relevant
def validate_input(user_message,conversation) -> bool:
    """
    Determines whether the user's message is medically relevant.
    Returns True if relevant, False otherwise.
    """
    validation_prompt = [
        relevance_check,
        {"role": "user", "content": (f"User input: {user_message}\nIs this medically relevant? Respond with 'true' or 'false' only."
                                     "if the answer is yes or no, consider it as relevant"
                                     "keep in mind the user might be answering questions")}
    ]
    
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=validation_prompt + conversation,
        response_format=InputValidation,
    )
    
    return completion.choices[0].message.parsed.is_relevant

# Function to extract doctor from user symptoms
def extract_doctor(conversation) -> DoctorExtraction:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=DoctorExtraction,
    )
    return completion.choices[0].message.parsed

# Function to create the next question to ask the user
def ask_question(conversation) -> Questions:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=Questions,
    )
    return completion.choices[0].message.parsed

# Function to extract if the symptoms of the user are not very severe
def extract_symptoms_not_severe(conversation) -> SymptomsNotSevere:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=SymptomsNotSevere,
    )
    return completion.choices[0].message.parsed

# Function to check if the user symptoms require urgent care
def check_urgent_attention(conversation) -> UrgentAttention:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=UrgentAttention,
    )
    return completion.choices[0].message.parsed

# Function to check if the user asks directly for an appointment with a doctor
def check_request_for_doctor(conversation) -> RequestDoctor:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=RequestDoctor,
    )
    return completion.choices[0].message.parsed

# Function to check if the user needs disabled access
def check_disabled_access(user_message) -> DisabledAccess:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages= [{"role": "system", "content": ("The user will tell if they need pwd access"
                                                  "they will probably answer with 'yes' or 'no'"
                                                  "does the user need pwd access?"
                                                  "does the user need easy access because of a disability?")}] + 
                                                  [{"role": "user", "content": user_message}],
        response_format=DisabledAccess,
    )
    return completion.choices[0].message.parsed

# get the closest specialty from the database
def get_closest_specialty(specialty):
    # fetch all specialties from the database
    db = get_db_connection("login_user")
    cursor = db.cursor()
    query = """SELECT DISTINCT(specialty) FROM doctors"""
    cursor.execute(query)
    specialties = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()

    matches = get_close_matches(specialty, specialties, n=1, cutoff=0.7) # Checks if the extracted specialty is close to any specialty in the database

    return matches[0] if matches else None


def init_agent_route(app):
    @app.before_request 
    def before_request(): # Clear conversation
        if request.method == 'GET':
            global conversation
            conversation = [system_message]
            global added_history
            added_history = False

    @app.route('/agent', methods=['GET', 'POST'])
    def agent_page():
        if 'user_id' not in session:
            return redirect(url_for('login')) # Redirect if not logged in

        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
        
        global conversation # Conversation history

        # If patient medical record and family history haven't be loaded yet
        global added_history
        if not added_history: 
            # Query to get relevant information for medical record and family history
            query = """
                SELECT age, gender, medical_record, family_history
                FROM patients
                WHERE patient_id = %s
            """
            conn = get_db_connection("patient_history")
            cur = conn.cursor()
            cur.execute(query, (session['user_id'],))
            user_history = cur.fetchall()
            cur.close()
            conn.close()

            # Create proper message that includes medical record and family history
            age, gender, medical_record, family_history = user_history[0]
            answer = f"I can see that you are a {gender}, {age} years of age."
            answer1 = ""
            if medical_record != None:
                answer1 = f" Your medical record consists of: {medical_record}."
            answer2 = ""
            if family_history != None:
                answer2 = f" Your family history includes: {family_history}."
            history = answer + answer1 + answer2 + " What are your symptoms?"
            conversation.append({"role": "assistant", "content": history})
            added_history = True

        if request.method == 'POST':
            conversation = eval(request.form['conversation'])  # Convert string back to list
            user_message = request.form['user_message'] # Get user input

            # Validate user input. If user input is irelevant don't add it to the conversation history
            if not validate_input(user_message, conversation):
                answer = "Your response does not seem to be related to medical symptoms. Please provide relevant information."
                conversation.append({"role": "assistant", "content": answer})
                return render_template('agent.html', conversation=conversation)
            
            # Add users input to the conversation history
            conversation.append({"role": "user", "content": user_message})
            
            # Check if user's symptoms require urgent care
            urgent_check = check_urgent_attention(conversation)
            if urgent_check.is_urgent and urgent_check.confidence_score > 0.95:
                answer = f"EMERGENCY: {urgent_check.reason}. Please go to the ER immediately!"
                conversation.append({"role": "assistant", "content": answer})
                return render_template('agent.html', conversation=conversation)

            # Check if user requested a specific doctor
            request_doctor = check_request_for_doctor(conversation)
            if request_doctor.confidence_score > 0.95 and request_doctor.specialty != None:
                # Check for the specialty in the database
                request_doctor.specialty = get_closest_specialty(request_doctor.specialty)
                if request_doctor.specialty is not None:
                    # Check if the user needs pwd access
                    if 'waiting_for_pwd' in session and session['waiting_for_pwd']: # At first pass this is false
                        need_pwd = check_disabled_access(user_message)
                        if need_pwd.is_disabled:
                            conversation.append({"role": "assistant", "content": "I have noted that you need PWD (people with disabilities) access. Let's move on with booking"})
                        else:
                            conversation.append({"role": "assistant", "content": "Great! Let's move on with booking"})
                        session['need_pwd'] = need_pwd.is_disabled
                        session['waiting_for_pwd'] = False # Reset flag
                        return render_template('agent.html', conversation=conversation, button = True)
                    conversation.append({"role": "assistant", "content": f"I see. You a want an appointment with a doctor who is a(n) {request_doctor.specialty}."})
                    conversation.append({"role": "assistant", "content": "Do you need PWD (people with disabilities) access?"})
                    session['waiting_for_pwd'] = True # Initialize flag
                    session['specialty'] = request_doctor.specialty
                    return render_template('agent.html', conversation=conversation)
                else: 
                    conversation.append({"role": "assistant", "content": "I wasn't able to identify a relevant specialist. Can you describe your symptoms in more detail?"})
                    return render_template('agent.html', conversation=conversation)

            # Check if the agent can extract confidently a specialty
            doctor_extraction = extract_doctor(conversation)
            if doctor_extraction.confidence_score > 0.9 and doctor_extraction.specialty != None:
                # find the closest specialty in the database
                print(doctor_extraction.specialty)
                doctor_extraction.specialty = get_closest_specialty(doctor_extraction.specialty)
                if doctor_extraction.specialty is not None:
                     # Check if the user needs pwd access
                    if 'waiting_for_pwd' in session and session['waiting_for_pwd']:
                        need_pwd = check_disabled_access(user_message)
                        if need_pwd.is_disabled:
                            conversation.append({"role": "assistant", "content": "I have noted that you need PWD (people with disabilities) access. Let's move on with booking"})
                        else:
                            conversation.append({"role": "assistant", "content": "Great! Let's move on with booking"})
                        session['need_pwd'] = need_pwd.is_disabled
                        session['waiting_for_pwd'] = False # Reset flag
                        return render_template('agent.html', conversation=conversation, button=True)
                    conversation.append({"role": "assistant", "content": f"You might have {doctor_extraction.diagnosis}. I recommend seeing a {doctor_extraction.specialty}."})
                    conversation.append({"role": "assistant", "content": "Do you need PWD (people with disabilities) access?"})
                    session['waiting_for_pwd'] = True # Initialize flag
                    session['specialty'] = doctor_extraction.specialty
                    return render_template('agent.html', conversation=conversation, button=True)
                else:
                    conversation.append({"role": "assistant", "content": "I wasn't able to identify a relevant specialist. Can you describe your symptoms in more detail?"})
                    return render_template('agent.html', conversation=conversation)
            
            # If after some questions there is no clear specialty needed, check if symptoms are not severe
            if len(conversation) > 8:
                not_severe_symptoms = extract_symptoms_not_severe(conversation)
                if not_severe_symptoms.confidence_score > 0.9:
                    treatment = not_severe_symptoms.at_home_treatment
                    conversation.append({"role": "assistant", "content": f"Based on your symptoms, you might not have a severe condition. I recommend {treatment}."})
                    return render_template('agent.html', conversation=conversation)
            
            # Ask next question
            question = ask_question(conversation)
            conversation.append({"role": "assistant", "content": question.question})
        return render_template('agent.html', conversation=conversation)