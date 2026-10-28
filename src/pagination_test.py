import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load the key from the .env file in the project root (one folder above src)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("Missing SUPABASE_URL or SUPABASE_KEY in the .env file.")

URL = f"{SUPABASE_URL}/rest/v1/notices"
PAGE_SIZE = 10        # small pages
MAX_PAGES = 5         # test only the first 5 pages (50 records)
PAUSE_SECONDS = 1     # be polite: wait between requests

session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "apikey": SUPABASE_KEY,
})

seen_ids = set()
duplicate_count = 0
total_records = 0

for page in range(MAX_PAGES):
    offset = page * PAGE_SIZE

    params = {
        "select": "id,title,schedule_time",
        "order": "schedule_time.desc,id.asc",  # id breaks ties for a stable order
        "limit": PAGE_SIZE,
        "offset": offset,
    }

    # Ask for an exact total count on the first page only
    extra_headers = {}
    if page == 0:
        extra_headers["Prefer"] = "count=exact"

    print(f"\n--- Page {page + 1} (offset {offset}) ---")

    try:
        response = session.get(URL, params=params, headers=extra_headers, timeout=20)
    except requests.RequestException as exc:
        print("Request failed:", exc)
        break

    print("Status:", response.status_code)
    print("Content-Range:", response.headers.get("Content-Range"))

    if response.status_code in (403, 429):
        print("Access refused or rate limited. Stopping, as agreed.")
        break

    if not response.ok:
        print("Response:", response.text[:400])
        break

    data = response.json()
    print("Records returned:", len(data))

    if data:
        print("First:", data[0]["title"])
        print("Last: ", data[-1]["title"])

    for record in data:
        total_records += 1
        if record["id"] in seen_ids:
            duplicate_count += 1
        seen_ids.add(record["id"])

    if len(data) < PAGE_SIZE:
        print("Fewer records than a full page: this is the last page.")
        break

    time.sleep(PAUSE_SECONDS)

print("\n=== Summary ===")
print("Records fetched:", total_records)
print("Unique IDs:", len(seen_ids))
print("Duplicates seen:", duplicate_count)