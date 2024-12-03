import os
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

# Configure the Gemini API with the API key
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Access the API key
api_key = os.getenv("API_KEY")

genai.configure(api_key=api_key)   # Replace with your API key

app = FastAPI()

# Initial list of general topics
topics = [
    "Project Deadlines",
    "Work meetings",
    "Learning Opportunities",
    "Entertainment",
    "Informal Meetings",
    "Technology Updates",
    "Career opportunities",
    "Online shopping",
    "Health and Fitness",
    "Social Media Notifications"
]

class GeneralPreferencesInput(BaseModel):
    preferences: Dict[str, int]

class TopPreferencesInput(BaseModel):
    top_preferences: List[str]

class SpecificPreferencesInput(BaseModel):
    preferences: Dict[str, int]

@app.get("/general-topics")
def get_general_topics():
    """Retrieve the list of general topics."""
    return {"topics": topics}

@app.post("/general-preferences")
def submit_general_preferences(input: GeneralPreferencesInput):
    """Submit user rankings for general topics and get top preferences."""
    general_preferences = input.preferences
    # Validate the preferences
    if len(general_preferences) != len(topics):
        raise HTTPException(status_code=400, detail="All topics must be ranked.")
    # Check for duplicate ranks
    ranks = list(general_preferences.values())
    if len(set(ranks)) != len(ranks):
        raise HTTPException(status_code=400, detail="Ranks must be unique.")
    # Sort the preferences
    sorted_preferences = sorted(general_preferences.items(), key=lambda x: x[1])
    top_preferences = [topic for topic, rank in sorted_preferences[:5]]
    # Save the general preferences to a JSON file
    with open("docs/general_preferences.json", "w", encoding="utf-8") as file:
        json.dump(general_preferences, file, indent=4)
    return {"top_preferences": top_preferences}

def clean_response_string(response_text):
    """Clean and parse the response string from Gemini."""
    try:
        response = response_text.strip()
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        json_text = response[start_idx:end_idx]
        cleaned_data = json.loads(json_text)
        return cleaned_data
    except json.JSONDecodeError as e:
        return None
    except Exception as e:
        return None

@app.post("/specific-topics")
def get_specific_topics(input: TopPreferencesInput):
    """Fetch specific topics from Gemini based on top preferences."""
    top_preferences = input.top_preferences
    # Generate the prompt for Gemini
    prompt = (
        f"You are an intelligent assistant. You will be given names of five categories that are very important to the user in his mail inbox. For better understanding of these preferences, prepare a more detailed list of 10 categories that might be present in his inbox. Top preferences:\n\n"
    )
    for idx, topic in enumerate(top_preferences, 1):
        prompt += f"{idx}. {topic}\n\n"

    prompt += "Provide the suggestions as a JSON array of strings."

    try:
        # Send the request to Gemini
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-8b")
        response = model.start_chat(history=[]).send_message(prompt)
        # Parse the response
        specific_topics = clean_response_string(response.text)
        if not specific_topics:
            raise HTTPException(status_code=500, detail="Failed to parse response from Gemini.")
        return {"specific_topics": specific_topics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/specific-preferences")
def submit_specific_preferences(input: SpecificPreferencesInput):
    """Submit user rankings for specific topics."""
    specific_preferences = input.preferences
    # Validate the preferences
    if len(specific_preferences) != 10:
        raise HTTPException(status_code=400, detail="All specific topics must be ranked.")
    # Check for duplicate ranks
    ranks = list(specific_preferences.values())
    if len(set(ranks)) != len(ranks):
        raise HTTPException(status_code=400, detail="Ranks must be unique.")
    # Save the specific preferences to a JSON file
    with open("docs/specific_preferences.json", "w", encoding="utf-8") as file:
        json.dump(specific_preferences, file, indent=4)
    return {"message": "Specific preferences saved successfully."}
