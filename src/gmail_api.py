import os
import json
import time
import base64
from datetime import datetime, timedelta
from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rich.console import Console

# Initialize the console for styled output
console = Console()

# Scopes for Gmail API
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar",
]

def get_unread_emails_logic():
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

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)

        # Calculate the Unix timestamp for 2 days ago
        two_days_ago = datetime.utcnow() - timedelta(days=2)
        two_days_ago_timestamp = int(two_days_ago.timestamp())

        # Query unread primary emails from the last 2 days
        query = f"is:unread category:primary after:{two_days_ago_timestamp}"
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])

        if not messages:
            return {"emails": []}

        email_data = []  # List to store email data

        # Fetch details of each unread primary email
        for message in messages[:10]:  # Limit to first 10 unread primary emails
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()

            headers = msg["payload"]["headers"]
            body = ""

            # Extract email subject and sender
            subject = next(
                (header["value"] for header in headers if header["name"] == "Subject"),
                "No Subject",
            )
            sender = next(
                (header["value"] for header in headers if header["name"] == "From"),
                "Unknown Sender",
            )

            # Extract email body
            if "data" in msg["payload"]["body"]:
                body = msg["payload"]["body"]["data"]
            elif "parts" in msg["payload"]:
                body = get_email_body(msg["payload"]["parts"])

            # Decode body from Base64
            if body:
                body = base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")

            # Add email details to the list
            email_data.append(
                {
                    "id": message["id"],
                    "subject": subject,
                    "sender": sender,
                    "body": body.strip(),
                }
            )

        # Optionally, save data to a JSON file
        with open("docs/emails.json", "w") as json_file:
            json.dump(email_data, json_file, indent=4)

        return {"emails": email_data}

    except HttpError as error:
        raise HTTPException(status_code=500, detail=f"An error occurred: {error}")

def get_email_body(parts):
    """Recursively retrieve the plain text body of an email."""
    for part in parts:
        mime_type = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data", "")
        if mime_type == "text/plain" and data:
            return data
        elif mime_type == "text/html" and data:
            return data
        elif "parts" in part:
            result = get_email_body(part["parts"])
            if result:
                return result
    return ""
