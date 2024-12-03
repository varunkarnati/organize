from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import os, uvicorn
# Importing functions and classes from the separate modules
from src.preferences_api import (
    get_general_topics,
    submit_general_preferences,
    get_specific_topics,
    submit_specific_preferences,
    GeneralPreferencesInput,
    TopPreferencesInput,
    SpecificPreferencesInput,
)

from src.gmail_api import get_unread_emails_logic
from src.gemini import organize
from src.tasks import get_tasks
from src.calendars import update_calendar

app = FastAPI()

# Routes for Gemini AI functionality

@app.get("/general-topics")
def get_general_topics_():
    """Retrieve the list of general topics."""
    return get_general_topics()

@app.post("/general-preferences")
def submit_general_preferences_(input: GeneralPreferencesInput):
    """Submit user rankings for general topics and get top preferences."""
    return submit_general_preferences(input)

@app.post("/specific-topics")
def get_specific_topics_(input: TopPreferencesInput):
    """Fetch specific topics from Gemini based on top preferences."""
    return get_specific_topics(input)

@app.post("/specific-preferences")
def submit_specific_preferences_(input: SpecificPreferencesInput):
    """Submit user rankings for specific topics."""
    return submit_specific_preferences(input)




@app.get("/emails")
def get_unread_emails():
    """Fetch unread primary emails from the last 2 days."""
    print("reading emails")
    return get_unread_emails_logic()

@app.get("/organizer")
def get_unread_emails():
    """Fetch unread primary emails from the last 2 days."""
    organize()
    get_tasks()
    update_calendar()
    return "success"
