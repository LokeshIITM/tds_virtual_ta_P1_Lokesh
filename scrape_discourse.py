import requests
import json
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

headers = {
    "Cookie": os.getenv("DISCOURSE_COOKIE"),  # ✅ Securely load from .env
    "User-Agent": "Mozilla/5.0"
}

base_url = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34.json?page="

all_posts = []

for page in range(1, 501):  # 🔁 Max 500, will stop early if no content
    print(f"Fetching page {page}")
    url = base_url + str(page)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        all_posts.append(data)
        time.sleep(1)  # ⏱️ Be gentle to avoid rate-limiting
    elif response.status_code in [403, 404]:
        print(f"❌ Reached end at page {page}")
        break
    else:
        print(f"⚠️ Unexpected error at page {page}: {response.status_code}")
        break

# ✅ Save all collected posts
with open("tds_discourse.json", "w", encoding="utf-8") as f:
    json.dump(all_posts, f, indent=2)

print("✅ Scraping complete.")
