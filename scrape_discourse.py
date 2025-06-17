import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

DISCOURSE_COOKIE = os.getenv("DISCOURSE_COOKIE")
HEADERS = {
    "Cookie": DISCOURSE_COOKIE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" # More specific User-Agent
}

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = 34  # TDS KB category
all_posts = []
page = 1
MAX_RETRIES = 5
INITIAL_DELAY = 1 # seconds

print("🔍 Starting TDS Discourse scrape...")

while True:
    category_url = f"{BASE_URL}/c/courses/tds-kb/{CATEGORY_ID}.json?page={page}"
    print(f"📄 Fetching topic list page {page}...")
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            r = requests.get(category_url, headers=HEADERS, timeout=10) # Add a timeout
            if r.status_code == 200:
                break # Success, break out of retry loop
            elif r.status_code == 429:
                print(f"⚠️ Rate limited. Waiting for {INITIAL_DELAY * (2 ** retries)} seconds...")
                time.sleep(INITIAL_DELAY * (2 ** retries)) # Exponential backoff
                retries += 1
            else:
                print(f"❌ Failed to fetch page {page} with status code {r.status_code}. Retrying...")
                time.sleep(INITIAL_DELAY * (2 ** retries))
                retries += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ An error occurred: {e}. Retrying...")
            time.sleep(INITIAL_DELAY * (2 ** retries))
            retries += 1
    
    if retries == MAX_RETRIES:
        print(f"❌ Max retries reached for page {page}. Giving up.")
        break

    data = r.json()
    topics = data.get("topic_list", {}).get("topics", [])
    if not topics:
        print("✅ No topics found on this page. Stopping.")
        break

    for topic in topics:
        topic_id = topic["id"]
        slug = topic["slug"]
        topic_title = topic.get("title", "")
        topic_url = f"{BASE_URL}/t/{slug}/{topic_id}.json"

        print(f"  🔗 Fetching topic: {topic_title}")
        
        topic_retries = 0
        while topic_retries < MAX_RETRIES:
            try:
                tr = requests.get(topic_url, headers=HEADERS, timeout=10) # Add a timeout
                if tr.status_code == 200:
                    break # Success, break out of retry loop
                elif tr.status_code == 429:
                    print(f"    ⚠️ Topic rate limited. Waiting for {INITIAL_DELAY * (2 ** topic_retries)} seconds...")
                    time.sleep(INITIAL_DELAY * (2 ** topic_retries))
                    topic_retries += 1
                else:
                    print(f"    ⚠️ Failed to fetch topic {topic_id} with status code {tr.status_code}. Retrying...")
                    time.sleep(INITIAL_DELAY * (2 ** topic_retries))
                    topic_retries += 1
            except requests.exceptions.RequestException as e:
                print(f"    ❌ An error occurred fetching topic: {e}. Retrying...")
                time.sleep(INITIAL_DELAY * (2 ** topic_retries))
                topic_retries += 1

        if topic_retries == MAX_RETRIES:
            print(f"    ❌ Max retries reached for topic {topic_id}. Skipping.")
            continue

        topic_data = tr.json()
        posts = topic_data.get("post_stream", {}).get("posts", [])
        combined_text = "\n\n".join([p.get("cooked", "") for p in posts])

        all_posts.append({
            "title": topic_title,
            "url": f"{BASE_URL}/t/{slug}/{topic_id}",
            "content": combined_text
        })

        time.sleep(0.5) # Increased delay for individual topics

    if "more_topics_url" not in data.get("topic_list", {}):
        print("✅ All topic pages fetched.")
        break

    page += 1
    time.sleep(1) # Increased delay for category pages

# Save to file
output_path = "tds_discourse.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_posts, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done! {len(all_posts)} topics saved to {output_path}")