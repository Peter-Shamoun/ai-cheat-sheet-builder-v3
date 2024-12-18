import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
import requests
import json

# Get the user ID from the API
def get_user_id():
    try:
        response = requests.get('http://localhost:5000/current-user')
        if response.status_code == 200:
            data = response.json()
            return data['userId']
        else:
            raise Exception(f"Failed to get user ID. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error getting user ID: {e}")
        return None

user_id = get_user_id()
print(f"Current user ID: {user_id}")

# The URL for your API endpoint
url = "https://3bjkmwezxb.execute-api.us-east-1.amazonaws.com/dev/extract-text"

# The JSON payload containing the user_id
payload = {
    "user_id": "user_"+user_id
}

# Set the headers to indicate that we're sending JSON
headers = {
    "Content-Type": "application/json"
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

# Print the status code and the response from the server
print("Status Code:", response.status_code)
print("Response:", response.text)

# If the response is JSON, you could also do:
try:
    response_data = response.json()
    print("JSON Response:", json.dumps(response_data, indent=2))
except ValueError:
    # Not a JSON response
    pass
