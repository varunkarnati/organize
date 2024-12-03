import os
import json
import google.generativeai as genai
from rich.console import Console
from datetime import datetime
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Access the API key
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)  # Replace with your API key
console = Console()  # Initialize Rich console for rendering

def read_email_data(file_path):
    """Reads the email data from a JSON file."""
    try:
        with open(file_path, "r") as json_file:
            email_data = json.load(json_file)
        return email_data
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        console.print(f"[bold red]Error:[/bold red] The file '{file_path}' is not a valid JSON file.")
    return None

def read_user_preferences(preference_file):
    """Reads user preferences from a JSON file."""
    try:
        with open(preference_file, "r", encoding="utf-8") as json_file:
            preferences = json.load(json_file)
        return preferences
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] The file '{preference_file}' was not found.")
    except json.JSONDecodeError:
        console.print(f"[bold red]Error:[/bold red] The file '{preference_file}' is not a valid JSON file.")
    return {}

def generate_prompt(email_data, general_preferences, specific_preferences):
    """Generate a structured prompt based on the email data and user preferences."""
    # Add user preferences to the prompt
    prompt = (
        "You are an intelligent email assistant. Analyze the following categories in a ranked order given by the user."
        "The top 3 are the most important for the user. The next five are normal and the other 2 are the least preferred to the user.\n\n"
    )
    prompt += "User Preferences:\n"
    prompt += "General Preferences:\n" + json.dumps(general_preferences, indent=4) + "\n"
    prompt += "Specific Preferences:\n" + json.dumps(specific_preferences, indent=4) + "\n\n"

    # Add email data to the prompt
    for email in email_data:
        email_id = email.get('id', 'Unknown ID')
        sender = email.get('sender', 'Unknown Sender')
        subject = email.get('subject', 'No Subject')
        body = email.get('body', 'No Body')[:200]  # Truncate body for clarity

        prompt += (
            f"**Email ID:** {email_id}\n"
            f"**Sender:** {sender}\n"
            f"**Subject:** {subject}\n"
            f"**Body:** {body}...\n"
            "---\n"
        )

    # Add the rest of the prompt as before
    prompt += (
        "\nBased on the emails and user preferences:\n"
        "1. Categorize each email as most important, important, normal, or least important.\n"
        "2. Identify if the email requires one or more actionable tasks, follow-ups, or a reply.\n"
        "3. For emails with deadlines, include two entries: one for setting the task and another for scheduling the deadline in the calendar.\n"
        "4. If a reply is required, include it in the action details as part of the task.\n"
        "5. For example, if there are two meetings scheduled at the same time, then the most preferred category meeting should be scheduled and the other one should be tried to reschedule.\n"
        "6. If there are situations where there are some meeting invites and also there is a reply required for that same mail, then there should be one task added to reply and one calendar event should be added to join the meeting. REMEMBER to do this for such scenarios"
        "7. REPLY NEEDED mails should be added into tasks and also into calendar if necessary (like for meeting invites) as a separate document in the json output"
        "8. Respond in JSON format as specified below:\n\n"
        "Example JSON Output:\n"
        "[\n"
        "    {\n"
        "        \"email_id\": \"string\",        // Unique identifier or sender of the email\n"
        "        \"importance\": \"string\",     // One of: 'most important', 'important', 'normal', 'least important'\n"
        "        \"subject\": \"string\",        // The subject line of the email\n"
        "        \"action_type\": \"string\",    // Either 'task', 'calendar'\n"
        "        \"action_details\": {           // Details about the action to be taken\n"
        "            \"task\": \"string\",       // Task description, if applicable\n"
        "            \"reply_needed\": true,    // Whether a reply is required (true/false), if this is for a calender event then create a separate task for the same as a task category\n"
        "            \"reply_message\": \"string\", // Suggested reply message\n"
        f"            \"event_date\": \"string\", // Start date/time for calendar events . REMEMBER to USE correct date format used in Google Calendar API YYYY-MM-DDTHH:mm:ss±hh:mm  use this current date for references{datetime.now()}\n"
        "            \"event_end_date\": \"string\", // End date/time for calendar events .REMEMBER to USE  correct date format used in Google Calendar API YYYY-MM-DDTHH:mm:ss±hh:mm. If not mentioned set the duration as 1 hour\n"
        "            \"timezone\": \"string\"    // Timezone for calendar events use IST \n"
        "        }\n"
        "    }\n"
        "]\n"
    )
    return prompt

def clean_response_string(response_text):
    """Skips the first and last lines of the response string and parses it as JSON."""
    try:
        # Split the response into lines
        lines = response_text.split("\n")

        # Skip the first and last lines
        if len(lines) > 2:
            cleaned_lines = lines[1:-1]
        else:
            console.print("[bold red]Error:[/bold red] Response does not have enough lines to clean.")
            return None

        # Join the cleaned lines and parse as JSON
        cleaned_json_text = "\n".join(cleaned_lines)
        cleaned_data = json.loads(cleaned_json_text)  # Parse to verify it's valid JSON

        return cleaned_data
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error parsing response string as JSON:[/bold red] {e}")
        return None
    except Exception as e:
        console.print(f"[bold red]Unexpected error cleaning response string:[/bold red] {e}")
        return None

def process_emails_with_preferences(email_data, general_preferences, specific_preferences):
    """Pass email data and user preferences to Gemini API for processing."""
    if not email_data:
        console.print("[bold red]No email data to process.[/bold red]")
        return

    # Generate the prompt
    prompt = generate_prompt(email_data, general_preferences, specific_preferences)

    try:
        # Initialize the model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-8b")

        # Start a chat session
        chat_session = model.start_chat(history=[])

        # Send the message to the Gemini API
        response = chat_session.send_message(prompt)

        # Print the raw response for debugging
        console.print(f"[bold yellow]Raw Response:[/bold yellow]\n{response.text}")

        # Clean and parse the response
        clean_response = clean_response_string(response.text)
        if not clean_response:
            console.print("[bold red]Failed to clean and parse the response.[/bold red]")
            return

        # Save the structured actionable data to a JSON file
        json_file = os.path.join("docs", "categorized_emails_and_tasks.json")
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(clean_response, file, indent=4)
        console.print(f"[bold green]Structured actions saved to {json_file}[/bold green]")
        return json.dump(clean_response)

    except Exception as e:
        console.print(f"[bold red]Error communicating with Gemini API:[/bold red] {e}")

def organize():
    """Main function to process email data with preferences."""
    # Specify the paths to the JSON files
    email_file = os.path.join("docs", "emails.json")
    general_pref_file = os.path.join("docs", "general_preferences.json")
    specific_pref_file = os.path.join("docs", "specific_preferences.json")

    # Step 1: Read email data and preferences
    email_data = read_email_data(email_file)
    # email_data=json.loads(str(email_data))
    general_preferences = read_user_preferences(general_pref_file)
    specific_preferences = read_user_preferences(specific_pref_file)

    # Step 2: Process emails with preferences
    process_emails_with_preferences(email_data, general_preferences, specific_preferences)

