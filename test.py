import requests

# Define the endpoint URL
url = 'http://127.0.0.1:5000/predict_crops'

# Define the payload with necessary data
payload = {
    "latitude": 28.7041,
    "longitude": 77.1025,
    "sunlight": 6,
    "area": 500,
}

# Send the POST request
response = requests.post(url, json=payload)

# Print the response
print(response.json())