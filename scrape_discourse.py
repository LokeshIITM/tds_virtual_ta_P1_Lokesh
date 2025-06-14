import requests
import json
import time

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = 34  # TDS Knowledge Base (TDS Jan 2025)
MAX_PAGES = 10     # Adjust as needed (e.g. 10)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": "_gcl_au=1.1.126943287.1744429579; _ga=GA1.1.1211786600.1744429580; _fbp=fb.2.1744429579881.552111905237520651; _ga_5HTJMW67XK=GS2.1.s1749881002$o18$g0$t1749881002$j60$l0$h0; _ga_08NPRH5L4M=GS2.1.s1749881002$o25$g1$t1749881665$j60$l0$h0; _t=coAkdYRFvtYjJ2%2BkZg233jJoUXSmkWhS7QJ3b0unXmhYNgVBJRp7lH8UNiZA0j96svhQ7WWdKx%2BOA097VBkY3Mx8DA3Gg116Duw8pJOHNZj8QRutcM4BzfzVM96U3LPqUwpydtrpo7%2F7Oodsu8ETGNUbiAt%2FZg529on2X0PmDp5sAPjZ%2F6Q4Rr7KCKcGXY4z9dWJqzlvjHYARkrm5ViBHoxXRlUrzqVe8HdWwrMN35quICv33Rj2k1Yqqmdhfl3fcJ233mjOiDpuFjMTeVuzEX236Dk80qvDcElYSf2t%2BSRs54T5fMQChU1dMk50h0T0aZtT5P99oQk%3D--IwgWA0byqerP02ie--PzxvIWNi0heFV3cBmzTctA%3D%3D; _forum_session=vlF0NLnq4j%2F0gUOX2hMg7a8PhLIymy12ykube3k6app1K2qaqhAgWw%2BXv04YQgvmvb5M51Tfm32vtXMwfKoYwb8xs0vLbIJHMpTFJ9F3trmHRzESL832hbfQF8X4UEEE619SwJ%2FTaQoopULwWcCuHrEZq6GNDVD58hdlRWCjdxzyOcpbP750T5xF%2Fsl3gR8IoAIyL3bah4MWdN5SlRTekU5W2jNUAUAstzy2pm3dLbPFDkFgBkMePJPFBuK7asvi05eYHVlwCcaghun0EQ2YAkhT%2FHCG56cdxPFUkWDZkQ4PP5TR9uq42E7sv%2FUYald%2BMWmFS9ZeSTMmN6KrOSMH7IRu9aTVV9KKVlv8%2BLBxVb5H06Kthv8je4EZJmfrcw4tZgrVfnR4sLmBViXMjuNPcMguEYIe0PXpntHCgfXBVec%2B42WfF7fAAEhV5T7CX2ISweaAn3vpQwJ1jtlY3Xtqugue40UV2Q%3D%3D--Wd4nnH%2F%2B4pmiISlF--a1zJ2Be8XO7nxMHBS4yRnA%3D%3D"  # Copy from browser DevTools
}

all_posts = []

for page in range(1, MAX_PAGES + 1):
    print(f"Fetching page {page}")
    url = f"{BASE_URL}/c/courses/tds-kb/{CATEGORY_ID}.json?page={page}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Error:", response.status_code)
        break

    topics = response.json().get("topic_list", {}).get("topics", [])

    for topic in topics:
        topic_url = f"{BASE_URL}/t/{topic['slug']}/{topic['id']}.json"
        print("  ->", topic_url)
        topic_response = requests.get(topic_url, headers=headers)
        if topic_response.status_code == 200:
            data = topic_response.json()
            all_posts.append({
                "url": topic_url,
                "title": data.get("title"),
                "posts": [post["cooked"] for post in data["post_stream"]["posts"]]
            })

        time.sleep(1)  # Be polite to the server

# Save to JSON file
with open("tds_discourse.json", "w", encoding="utf-8") as f:
    json.dump(all_posts, f, indent=2, ensure_ascii=False)

print("✅ Scraping complete. Saved to tds_discourse.json")
