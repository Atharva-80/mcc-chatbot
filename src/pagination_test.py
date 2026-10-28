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
PAGE_SIZE = 10          # small pages
PAUSE_SECONDS = 1       # be polite: wait between requests
SAFETY_MAX_PAGES = 50   # never fetch more than 500 records in this test


def parse_total(content_range):
    """Turn '0-9/110' into 110. Returns None if the total is unknown ('*')."""
    if not content_range or "/" not in content_range:
        return None
    total_part = content_range.split("/")[-1]
    return int(total_part) if total_part.isdigit() else None


session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "apikey": SUPABASE_KEY,
})

total_expected = None
seen_ids = set()
duplicate_count = 0
total_records = 0
stopped_early = False

for page in range(SAFETY_MAX_PAGES):
    offset = page * PAGE_SIZE

    params = {
        "select": "id,title,schedule_time",
        "order": "schedule_time.desc,id.asc",  # id breaks ties for a stable order
        "limit": PAGE_SIZE,
        "offset": offset,
    }

    # Ask for an exact total count on the first page only
    extra_headers = {"Prefer": "count=exact"} if page == 0 else {}

    print(f"\n--- Page {page + 1} (offset {offset}) ---")

    try:
        response = session.get(URL, params=params, headers=extra_headers, timeout=20)
    except requests.RequestException as exc:
        print("Request failed:", exc)
        stopped_early = True
        break

    print("Status:", response.status_code)
    print("Content-Range:", response.headers.get("Content-Range"))

    if response.status_code in (403, 429):
        print("Access refused or rate limited. Stopping, as agreed.")
        stopped_early = True
        break

    if not response.ok:
        print("Response:", response.text[:400])
        stopped_early = True
        break

    if page == 0:
        total_expected = parse_total(response.headers.get("Content-Range"))
        print("Total reported by the API:", total_expected)

    data = response.json()
    print("Records returned:", len(data))

    for record in data:
        total_records += 1
        if record["id"] in seen_ids:
            duplicate_count += 1
        seen_ids.add(record["id"])

    if len(data) < PAGE_SIZE:
        print("Fewer records than a full page: this is the last page.")
        break

    if total_expected is not None and total_records >= total_expected:
        print("Reached the total reported by the API.")
        break

    time.sleep(PAUSE_SECONDS)
else:
    # This runs only if the loop ended without a break
    print("Safety limit reached. Stopping.")
    stopped_early = True

print("\n=== Summary ===")
print("Total reported by the API:", total_expected)
print("Records fetched:", total_records)
print("Unique IDs:", len(seen_ids))
print("Duplicates seen:", duplicate_count)
print("Stopped early:", stopped_early)
if total_expected is not None:
    print("Fetched matches reported total:", total_records == total_expected)