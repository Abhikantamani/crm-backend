import requests

# 1. Using the same universal testing server
test_url = "https://httpbin.org/post"

# 2. The exact Support data your bot currently collects
fake_ticket_data = {
    "email": "kantamani.abhiram@gmail.com",
    "issue": "The screen just goes blank"
}

print("Sending Support Ticket data to the test database...")

# 3. Sending the POST request
response = requests.post(test_url, json=fake_ticket_data)

# 4. Check if it worked
if response.status_code == 200:
    print("Success! The server received your ticket and echoed it back:")
    print(response.json()["data"])
else:
    print("Oops, something went wrong. Status Code:", response.status_code)