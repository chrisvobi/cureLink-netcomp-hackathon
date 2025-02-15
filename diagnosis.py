from openai import OpenAI
from pydantic import BaseModel, Field
import json

with open('config.json') as config_file:
    config = json.load(config_file)
    key = config['KEY']

class Doctor(BaseModel):
    specialty: str = Field(description="The doctor's specialty")

client = OpenAI(api_key = key)

# promts for medical questions and diagnosis
system_message = {
    "role": "system",
    "content": (
        "You are a medical AI assistant. When a user describes their symptoms, "
        "ask follow-up questions to get more details before making a diagnosis. "
        "After gathering enough information, suggest a possible diagnosis and "
        "recommend a relevant specialist. Remind the user that this is not a substitute for professional medical advice."
    ),
}

# init conversation
conversation = [system_message]

user_message = input("Please provide the symptoms: ")
conversation.append({"role": "user", "content": user_message})

specialty = None
key_words = ["doctor", "specialist", "physician", "diagnosis"]
agent_response = ""
while not any(key_word in agent_response.lower() for key_word in key_words):
    # get ai response
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=conversation
    )

    agent_response = completion.choices[0].message.content
    print(f"Agent: {agent_response}")
    conversation.append({"role": "assistant", "content": agent_response})

    user_message = input("Your response: ")
    conversation.append({"role": "user", "content": user_message})

print(conversation[-1])