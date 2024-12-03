import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from rich.console import Console

# Initialize the console for styled output
console = Console()

# Google Calendar API Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Authenticate and return the Google Calendar API service."""
    creds = None
    if os.path.exists('auth/token.json'):
        creds = Credentials.from_authorized_user_file('auth/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('auth/credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('auth/token.json', "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)
def add_event(service, event_data):
    """Add a single event to Google Calendar."""
    action_details = event_data.get("action_details", {})

    # Extract relevant fields from action_details
    event_date = action_details.get("event_date", "2024-11-22T10:00:00")
    event_end_date = action_details.get("event_end_date", "2024-11-22T11:00:00")
    timezone = action_details.get("timezone", "UTC")

    event_body = {
        "summary": event_data.get("subject", "No Subject"),
        "description": action_details.get("task", "No Task Description Provided"),
        "start": {
            "dateTime": event_date,
            "timeZone": timezone
        },
        "end": {
            "dateTime": event_end_date,
            "timeZone": timezone
        }
    }

    try:
        # Insert the event into the user's primary calendar
        print(event_body)
        service.events().insert(calendarId="primary", body=event_body).execute()
        console.print(f"[bold green]Event added:[/bold green] {event_body['summary']}")
    except Exception as e:
        console.print(f"[bold red]Failed to add event:[/bold red] {event_body['summary']} - {e}")

def update_calendar():
    # Path to the JSON file
    json_file = "docs/categorized_emails_and_tasks.json"

    # Load the JSON data
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] The file '{json_file}' was not found.")
        return
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error parsing JSON file:[/bold red] {e}")
        return

    # Authenticate with Google Calendar API
    service = authenticate_google_calendar()
    print("ucgvhb")

    # Process only calendar events
    for entry in data:
        if entry.get("action_type") == "calendar":
            add_event(service, entry)

# update_calendar()