import requests

url = "http://127.0.0.1:5000"

response = requests.post(
    f"{url}/api/chat",
    json={"question": "How can I find an internship?"}
)

print("CHAT RESPONSE:")
print(response.json())

if response.status_code == 200:
    conversation_id = response.json()["conversation_id"]

    history = requests.get(
        f"{url}/api/history/{conversation_id}"
    )

    print("\nCONVERSATION HISTORY:")
    print(history.json())
