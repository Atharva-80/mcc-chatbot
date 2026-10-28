import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Find the project root (one folder above src) and load the .env file there
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("Missing SUPABASE_URL or SUPABASE_KEY in the .env file.")

print("URL loaded: yes")
print("Key loaded: yes (value hidden)")

BASE_URL = f"{SUPABASE_URL}/rest/v1"

TESTS = {
    "General notices": (
        f"{BASE_URL}/notices",
        {
            "select": "id,title,schedule_time",
            "order": "schedule_time.desc",
            "limit": 2,
        },
    ),
    "Junior college notices": (
        f"{BASE_URL}/jr_college_notices",
        {
            "select": "id,title,schedule_time",
            "order": "schedule_time.desc",
            "limit": 2,
        },
    ),
    "Calendar records": (
        f"{BASE_URL}/notices",
        {
            "select": (
                "calendar_title,calendar_date,"
                "calendar_category,calendar_venue,calendar_time"
            ),
            "publish_calendar": "eq.true",
            "calendar_date": "not.is.null",
            "limit": 2,
        },
    ),
}

session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "apikey": SUPABASE_KEY,
})

for name, (url, params) in TESTS.items():
    print(f"\n--- {name} ---")

    try:
        response = session.get(url, params=params, timeout=20)

        print("Status:", response.status_code)
        print("Content-Range:", response.headers.get("Content-Range"))

        if response.ok:
            data = response.json()
            print("Records returned:", len(data))

            for record in data:
                print(record)
        else:
            print("Response:", response.text[:400])

    except requests.RequestException as exc:
        print("Request failed:", exc)