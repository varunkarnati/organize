import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from rich.console import Console

# Initialize the console for styled output
console = Console()

# Google Tasks API Scopes
SCOPES = ['https://www.googleapis.com/auth/tasks','https://www.googleapis.com/auth/calendar']

def authenticate_google_tasks():
    """Authenticate and return the Google Tasks API service."""
    creds = None
    token_file = "auth/token.json"
    credentials_file = "auth/credentials.json"

    # Check if the token.json file exists
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            console.print("[bold green]Loaded credentials from token.json[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error loading credentials from {token_file}:[/bold red] {e}")
            creds = None

    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                console.print("[bold green]Access token refreshed successfully.[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error refreshing access token:[/bold red] {e}")
                creds = None  # Force re-authentication
        else:
            console.print("[bold yellow]No valid credentials available. Starting authentication flow.[/bold yellow]")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES
                )
                creds = flow.run_local_server(
                    port=3000, access_type='offline', prompt='consent'
                )
                console.print("[bold green]Authentication successful.[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error during authentication:[/bold red] {e}")
                return None

        # Save the credentials for the next run
        if creds:
            with open(token_file, "w") as token:
                token.write(creds.to_json())
            console.print(f"[bold green]Credentials saved to {token_file}.[/bold green]")

    # Build the Google Tasks API service
    try:
        service = build("tasks", "v1", credentials=creds)
    except Exception as e:
        console.print(f"[bold red]Error building Google Tasks service:[/bold red] {e}")
        return None

    return service

def add_task(service, task_data):
    """Add a single task to Google Tasks."""
    task_list_id = "@default"  # Use the default task list
    action_details = task_data.get("action_details", {})

    # Build the task notes
    task_notes = action_details.get("task", "No Task Details Provided")
    if action_details.get("reply_needed", False):
        reply_message = action_details.get("reply_message", "No reply message provided.")
        task_notes += f"\n\n[Reply Needed]\nSuggested Reply: {reply_message}"

    # Create the task body
    task_body = {
        "title": task_data.get("subject", "No Subject"),
        "notes": task_notes
    }

    try:
        service.tasks().insert(tasklist=task_list_id, body=task_body).execute()
        console.print(f"[bold green]Task added:[/bold green] {task_body['title']}")
    except Exception as e:
        console.print(f"[bold red]Failed to add task:[/bold red] {task_body['title']} - {e}")

def get_tasks():
    """Load tasks from JSON and add them to Google Tasks."""
    # Path to the JSON file
    json_file = "docs/categorized_emails_and_tasks.json"

    # Load the JSON data
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        console.print("[bold green]Loaded tasks from JSON file.[/bold green]")
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] The file '{json_file}' was not found.")
        return
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error parsing JSON file:[/bold red] {e}")
        return

    # Authenticate with Google Tasks API
    service = authenticate_google_tasks()
    if service is None:
        console.print("[bold red]Failed to authenticate with Google Tasks API.[/bold red]")
        return

    # Process only tasks with specified importance
    for entry in data:
        if entry.get("action_type") == "task":
            importance = entry.get("importance", "").lower()
            if importance in ["important", "most important"]:
                add_task(service, entry)


