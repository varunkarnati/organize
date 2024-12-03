# Organize

This project provides an API for managing tasks, preferences, and other features. Follow the instructions below to set up and run the project.

---

## Installation Instructions

### 1. Clone the Repository
Clone this repository to your local machine:

```bash
git clone https://github.com/varunkarnati/organize.git
cd api
```
2. Set Up the Environment
Install Required Python Packages
Ensure you have Python installed. Then, create a virtual environment and install the required packages:

```bash

# Create a virtual environment
python -m venv venv
```
# Activate the virtual environment
# On Windows:
```
venv\Scripts\activate
```
# On macOS/Linux:
```
source venv/bin/activate
```

# Install the dependencies
```
pip install -r requirements.txt
```
3. Download the credentials.json File
To enable API functionalities (e.g., Google API integration), download the credentials.json file from your Google Cloud project:

Log in to the Google Cloud Console.
Navigate to APIs & Services > Credentials.
Download the credentials.json file for your project.
Place the file in the root directory of this project.
4. Configure API Keys
Create a .env file in the root directory of the project and add the API key:

```
API_KEY=your_api_key_here
```
Replace your_api_key_here with the actual API key.

5. Run the Project
Start the API server:

# On Windows
```
uvicorn main:app --reload
```

# On macOS/Linux
```
uvicorn main:app --reload
```
Access the API at http://127.0.0.1:8000.

Features
Manage tasks and preferences.
Integration with Google APIs (Calendar, Gmail, etc.).

# License
This project is licensed under the MIT License. See the LICENSE file for details.
