from openai import OpenAI
from pydantic import BaseModel, Field
import json

with open('config.json') as config_file:  # Make sure config.json is in the same directory
    config = json.load(config_file)
    key = config['KEY']

client = OpenAI(api_key = key)
model = 'gpt-4o-mini'

# system messages
system_message = {
    "role": "system",
    "content": (
        "You are a medical AI assistant. Your goal is to ask relevant follow-up questions "
        "before making a diagnosis or recommending a specialist. "
        "Only recommend a specialist when you are at least 90% confident. "
        "If unsure, keep asking questions to gather more information. "
        "Never make bold assumptions or provide a diagnosis too early."
        "If you are at least 90% confident that the symptoms are not severe,and you have ruled out that the patient needs a doctor, reccomend simple at home treatment."
    ),
}

# init conversation
conversation = [system_message]

# define the data models
class DoctorExtraction(BaseModel):
    diagnosis: str = Field(description="Possible diagnosis based on the user's symptoms")
    specialty: str = Field(description="Relevant doctor's specialty (e.g., 'Cardiologist')")
    confidence_score: float = Field(description="Confidence score (0-1) for recommending a doctor")

class SymptomsNotSevere(BaseModel):
    at_home_treatment: str = Field(description="Recommendation for at-home treatment, based on symptoms")
    confidence_score: float = Field(description="Confidence score (0-1) for recommending at-home treatment")
    

class Questions(BaseModel):
    question: str = Field(description="The question to ask the user")


# functions to interact with the AI model
def extract_doctor(conversation) -> DoctorExtraction:
    """
    Extracts the doctor's specialty to recommend based on the user's message
    """
    completion = client.beta.chat.completions.parse(
        model=model,
        messages= conversation,
        response_format=DoctorExtraction,
    )
    result = completion.choices[0].message.parsed
    return result

def ask_question(conversation) -> Questions:
    """
    Asks a follow-up question to the user
    """
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=Questions,
    )
    result = completion.choices[0].message.parsed
    return result

def extract_symptoms_not_severe(conversation) -> SymptomsNotSevere:
    """Extract the recommendation for at-home treatment"""
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=conversation,
        response_format=SymptomsNotSevere,
    )
    result = completion.choices[0].message.parsed
    return result

user_message = input("Please provide the symptoms: ")
conversation.append({"role": "user", "content": user_message})

specialty = None

while specialty is None:
    # first llm to extract doctor
    doctor_extraction = extract_doctor(conversation)
    if doctor_extraction.confidence_score > 0.9:
        conversation.append({"role": "assistant", "content": doctor_extraction})    
        specialty = doctor_extraction.specialty
        print(f"Based on your symtpom_severity, you might have {doctor_extraction.diagnosis}. I recommend seeing a {specialty}.")
        print(doctor_extraction)
        continue
        # extract at-home treatment
    if len(conversation) > 6:
        not_severe_symptoms = extract_symptoms_not_severe(conversation)
        if not_severe_symptoms.confidence_score > 0.9:
            conversation.append({"role": "assistant", "content":not_severe_symptoms})
            treatment = not_severe_symptoms.at_home_treatment
            print(f"Based on your symptoms, you might not have a severe condition. I recommend {treatment}.")
            print(treatment)
            break
    # ask follow-up question if doctor was not extracted
    question = ask_question(conversation)
    conversation.append({"role": "assistant", "content": question.question})
    print(f"Assistant: {question.question}")
    user_message = input("Your response: ")
    conversation.append({"role": "user", "content": user_message})

print("Conversation ended.")
