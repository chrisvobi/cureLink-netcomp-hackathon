from openai import OpenAI
from pydantic import BaseModel, Field
import json

model = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo-0125" , "gpt-4o" is better, but more expensive

with open('config.json') as config_file:  # Make sure config.json is in the same directory
    config = json.load(config_file)
    key = config['KEY']
client = OpenAI(api_key=key)

class Doctor(BaseModel):
    """Determine doctor's specialty"""
    specialty: str = Field(description="The doctor's specialty")
    confidence_score: float = Field(description="The confidence score of the prediction, between 0 and 1")

# Function to be called by the AI
def suggest_specialty(specialty: str, confidence_score: float) -> str:
    """Suggest a doctor's specialty based on the confidence score."""
    return json.dumps({"specialty": specialty, "confidence_score": confidence_score})

# system messages
system_message = {
    "role": "system",
    "content": (
        "You are a medical AI assistant. When a user describes their symptoms, "
        "ask follow-up questions to get more details before making a diagnosis. "
        "Only suggest a specialty when you are highly confident (at least 90% sure). "
        "After gathering enough information, suggest a possible diagnosis and "
        "recommend a relevant specialist. Remind the user that this is not a substitute for professional medical advice."
    ),
}

# init conversation
conversation = [system_message]

user_message = input("Please provide the symptoms: ")
conversation.append({"role": "user", "content": user_message})

# Loop until confidence is high enough
while True:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversation,
            tools=[  # Define the function calling tool
                {
                    "type": "function",
                    "function": {
                        "name": "suggest_specialty",
                        "description": "Suggest a doctor's specialty when confidence is high.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "specialty": {
                                    "type": "string",
                                    "description": "The doctor's specialty.",
                                },
                                "confidence_score": {
                                    "type": "number",
                                    "description": "The confidence score of the prediction (0-1).",
                                },
                            },
                            "required": ["specialty", "confidence_score"],
                        },
                    },
                }
            ],
            tool_choice="auto",  # Let the model decide whether to call a function
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            # Handle function call
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "suggest_specialty":
                arguments = json.loads(tool_call.function.arguments)
                specialty = arguments["specialty"]
                confidence_score = arguments["confidence_score"]

                if confidence_score >= 0.9:
                    print(f"\nAI: Based on the symptoms, I recommend seeing a {specialty}.")
                    print(f"AI: My confidence score is: {confidence_score:.2f}")
                    print("AI: Please remember this is not a substitute for professional medical advice.")
                    break  # Exit the loop
                else:
                    # (Optional) Handle cases below threshold, if needed.  Could ask more.
                    print(f"AI: I need more information to make a confident recommendation (Confidence: {confidence_score:.2f}).")
                    conversation.append(response_message) #append the message
                    # The AI hasn't called the function with sufficient confidence
                    # So, we'll treat this as a regular turn and get its next question
                    continue
        else:
            # Regular AI response (a question)
            agent_response = response_message.content
            print(f"\nAI: {agent_response}")
            conversation.append({"role": "assistant", "content": agent_response})

            user_response = input("You: ")
            conversation.append({"role": "user", "content": user_response})

    except Exception as e:
        print(f"An error occurred: {e}")
        break