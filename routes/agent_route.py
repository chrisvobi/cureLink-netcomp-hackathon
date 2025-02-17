from openai import OpenAI
from pydantic import BaseModel, Field
import json

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
        "If unsure, keep asking questions to gather more information. "
        "Never make bold assumptions or provide a diagnosis too early."
        "If you are at least 90% confident that the symptoms are not severe, and you have ruled out that the patient needs a doctor, recommend simple at-home treatment."
    ),
}

conversation = [system_message]

class DoctorExtraction(BaseModel):
    diagnosis: str = Field(description="Possible diagnosis based on the user's symptoms")
    specialty: str = Field(description="Relevant doctor's specialty (e.g., 'Cardiologist')")
    confidence_score: float = Field(description="Confidence score (0-1) for recommending a doctor")

class UrgentAttention(BaseModel):
    is_urgent: bool = Field(description="True if the symptoms require immediate emergency attention, False otherwise")
    confidence_score: float = Field(description="Confidence score (0-1) for classifying symtoms as urgent")
    reason: str = Field(description="Brief reason why emergency attention is necessary")

class SymptomsNotSevere(BaseModel):
    at_home_treatment: str = Field(description="Recommendation for at-home treatment, based on symptoms")
    confidence_score: float = Field(description="Confidence score (0-1) for recommending at-home treatment")

class Questions(BaseModel):
    question: str = Field(description="The question to ask the user")

class InputValidation(BaseModel):
    is_relevant: bool = Field(description="Indicates whether the user's input is medically relevant")

class RequestDoctor(BaseModel):
    specialty: str = Field(description="Relevant doctor's specialty (e.g., 'Cardiologist') that the user requested")
    confidence_score: float = Field(description="Confidence score (0-1) for user asking for a doctor or appointment")


relevance_check ={
    "role": "system",
    "content": ("You are a medical assisant that classifies whether a given input is medically relevant."
    "User input must contain health related or medical terms.")
}
# Function to check if user input is relevant
def validate_input(user_message,conversation) -> bool:
    """
    Determines whether the user's message is medically relevant.
    Returns True if relevant, False otherwise.
    """
    validation_prompt = [
        relevance_check,
        {"role": "user", "content": f"User input: {user_message}\nIs this medically relevant? Respond with 'true' or 'false' only."}
    ]
    
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=validation_prompt + conversation,
        response_format=InputValidation,
    )
    
    return completion.choices[0].message.parsed.is_relevant

def extract_doctor(conversation) -> DoctorExtraction:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=DoctorExtraction,
    )
    return completion.choices[0].message.parsed

def ask_question(conversation) -> Questions:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=Questions,
    )
    return completion.choices[0].message.parsed

def extract_symptoms_not_severe(conversation) -> SymptomsNotSevere:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=SymptomsNotSevere,
    )
    return completion.choices[0].message.parsed

def check_urgent_attention(conversation) -> UrgentAttention:
    """
    Determines whether the user's symptoms require immediate emergency attention.
    If so, the assistant should direct the user to go to the ER immediately.
    """
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=UrgentAttention,
    )
    return completion.choices[0].message.parsed

def check_request_for_doctor(conversation) -> RequestDoctor:
    """
    Determines whether the user asked directly for an appointment with the doctor
    """
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=RequestDoctor,
    )
    return completion.choices[0].message.parsed


from flask import render_template, request, session, redirect, url_for

def init_agent_route(app):
    @app.route('/agent', methods=['GET', 'POST'])
    def agent_page():
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect if not logged in
        
        if session.get('user_type') != "patient":  
            return redirect(url_for('login'))  # Redirect doctors away
        
        global conversation # Conversation history

        # Retrieve existing conversation from the form submission
        if request.method == 'POST':
            conversation = eval(request.form['conversation'])  # Convert string back to list
            user_message = request.form['user_message']

             # Validate user input
            if not validate_input(user_message,conversation):
                answer = "Assistant: Your response does not seem to be related to medical symptoms. Please provide relevant information."
                conversation.append({"role": "assistant", "content": answer})
                return render_template('agent.html', conversation=conversation)
            
            conversation.append({"role": "user", "content": user_message})
            
            # Check if user's symptoms require urgent care
            urgent_check = check_urgent_attention(conversation)
            if urgent_check.is_urgent and urgent_check.confidence_score > 0.95:
                answer = f"EMERGENCY: {urgent_check.reason}. Please go to the ER immediately!"
                conversation.append({"role": "assistant", "content": answer})
                return render_template('agent.html', conversation=conversation)
                # Stop the loop as emergency action is needed

            # Check if user requested a specific doctor
            request_doctor = check_request_for_doctor(conversation)
            if request_doctor.confidence_score > 0.8 and request_doctor.specialty != None:
                conversation.append({"role": "assistant", "content": f"I see. You a want an appointment with a doctor who is an {request_doctor.specialty}."})
                session['specialty'] = request_doctor.specialty
                session['conversation'] = conversation
                return render_template('agent.html', conversation=conversation, button=True)

            # Check if the agent can extract confidently a specialty
            doctor_extraction = extract_doctor(conversation)
            if doctor_extraction.confidence_score > 0.9 and doctor_extraction.specialty != None:
                conversation.append({"role": "assistant", "content": f"You might have {doctor_extraction.diagnosis}. I recommend seeing a {doctor_extraction.specialty}."})
                session['specialty'] = doctor_extraction.specialty
                session['conversation'] = conversation
                return render_template('agent.html', conversation=conversation, button=True)
            
            # If after some questions there is no clear specialty needed, check if symptoms are not sever
            if len(conversation) > 12:
                not_severe_symptoms = extract_symptoms_not_severe(conversation)
                if not_severe_symptoms.confidence_score > 0.9:
                    treatment = not_severe_symptoms.at_home_treatment
                    conversation.append({"role": "assistant", "content": f"Based on your symptoms, you might not have a severe condition. I recommend {treatment}."})
                    return render_template('agent.html', conversation=conversation)
            
            # Ask next question
            question = ask_question(conversation)
            conversation.append({"role": "assistant", "content": question.question})
        return render_template('agent.html', conversation=conversation)
