import requests

headers = {
    "X-API-Key": "asdfghjkl",
    "Content-Type": "application/json"
}

data = {
    "message": "Test secure message",
    "channel": "a", 
    "channel_secret": "b"
}

response = requests.post(
    "http://localhost:5000/api/broadcast-to-channel",
    headers=headers,
    json=data
)

print(response.json())