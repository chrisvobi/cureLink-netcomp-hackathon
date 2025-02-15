from openai import OpenAI
from pydantic import BaseModel, Field
import json

with open('config.json') as config_file:
    config = json.load(config_file)
    key = config['KEY']

client = OpenAI(api_key = key)
model = 'gpt-4o-mini'

# promts for medical questions and diagnosis
system_message = {
    "role": "system",
    "content": (
        "You are a medical AI assistant. When a user describes their symptoms, "
        "ask follow-up questions to get more details before making a diagnosis. "
        "After gathering enough information, suggest a possible diagnosis and "
        "recommend only one (one word) relevant specialist. Remind the user that this is not a substitute for professional medical advice."
        "suggest a doctor after maximum 3 questions. "
    ),
}

# init conversation
conversation = [system_message]

# define the data models
class DoctorExtraction(BaseModel):
    diagnosis: str = Field(description="The possible diagnosis based on the user's symptoms")
    specialty: str = Field(description="The doctor's specialty to recommend")
    confidence_score: float = Field(description="The confidence score that you are ready to recommend the doctor between 0 and 1")

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


user_message = input("Please provide the symptoms: ")
conversation.append({"role": "user", "content": user_message})

specialty = None
while specialty is None:
    
    # first llm to extract doctor
    doctor_extraction = extract_doctor(conversation)
    if doctor_extraction.confidence_score > 0.5:
        conversation.append({"role": "assistant", "content": doctor_extraction})    
        specialty = doctor_extraction.specialty
        print(f"Based on your symptoms, you might have {doctor_extraction.diagnosis}. I recommend seeing a {specialty}.")
        print(doctor_extraction)
        continue
    
    # ask follow-up question if doctor was not extracted
    question = ask_question(conversation)
    conversation.append({"role": "assistant", "content": question.question})
    print(f"Assistant: {question.question}")
    user_message = input("Your response: ")
    conversation.append({"role": "user", "content": user_message})

print("Conversation ended.")