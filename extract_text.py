import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

user_id = os.getenv('CURRENT_USER_ID')
print(f"Current user ID: {user_id}")
def get_extracted_text():
    # The URL for your API endpoint
    url = "https://3bjkmwezxb.execute-api.us-east-1.amazonaws.com/dev/extract-text"

    # The JSON payload containing the user_id
    payload = {
        "user_id": "user_"+os.getenv('CURRENT_USER_ID')
    }

    # Set the headers to indicate that we're sending JSON
    headers = {
        "Content-Type": "application/json"
    }

    # Make the POST request
    response = requests.post(url, headers=headers, json=payload)

    # Print the status code and the response from the server
    print("Status Code:", response.status_code)

    # If the response is JSON, you could also do:
    try:
        response_data = response.json()
        print("JSON Response:", json.dumps(response_data, indent=2))
    except ValueError:
        # Not a JSON response
        pass
    return response.text
if __name__ == "__main__":
    response_text = get_extracted_text()
    print("Response:", response_text)