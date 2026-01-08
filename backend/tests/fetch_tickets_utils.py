import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")

ZENDESK_URL = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets.json"


def fetch_zendesk_tickets():
    auth = (ZENDESK_EMAIL, ZENDESK_API_TOKEN)

    print("🔄 Fetching tickets from Zendesk...")
    response = requests.get(ZENDESK_URL, auth=auth)

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return

    data = response.json()
    tickets = data.get("tickets", [])

    if not tickets:
        print("No tickets found.")
        return

    print(f"✅ Found {len(tickets)} ticket(s):\n")
    for t in tickets:
        print(f"ID: {t['id']}")
        print(f"Subject: {t['subject']}")
        print(f"Status: {t['status']}")
        print(f"Created At: {t['created_at']}")
        print(f"Tags: {t.get('tags', [])}")
        print("-" * 40)


if __name__ == "__main__":
    fetch_zendesk_tickets()
