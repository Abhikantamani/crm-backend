import requests

url = "http://127.0.0.1:8000/chat"

# THIS IS THE IMPORTANT PART (The Token)
headers = {
    "Authorization": "Bearer test_token_123",
    "Content-Type": "application/json"
}

# The new code only needs "message"
data = {
    "message": "Testing the new token bouncer!"
}

response = requests.post(url, headers=headers, json=data)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")