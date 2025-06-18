from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.responses import JSONResponse
import os
import json
import difflib

# ─────────────────────────────────────────────
# FastAPI app + simple health-check route
# ─────────────────────────────────────────────
app = FastAPI()

@app.get("/")
def read_root():
    return JSONResponse(content={"message": "TDS Virtual TA is live!"})

# ─────────────────────────────────────────────
# Environment & OpenAI client (via AI Proxy)
# ─────────────────────────────────────────────
load_dotenv()

client = OpenAI(
    api_key=os.getenv("AIPROXY_TOKEN"),
    base_url="https://aiproxy.sanand.workers.dev/openai"
)

# ─────────────────────────────────────────────
# Load scraped Discourse posts (local JSON)
# ─────────────────────────────────────────────
with open("tds_discourse.json", "r", encoding="utf-8") as f:
    discourse_posts: List[Dict] = json.load(f)

# ─────────────────────────────────────────────
# Request schema
# ─────────────────────────────────────────────
class Query(BaseModel):
    question: str
    image: Optional[str] = None  # not used yet but preserved

# ─────────────────────────────────────────────
# Utils: fuzzy search for relevant posts
# ─────────────────────────────────────────────
def find_relevant_posts(question: str, top_n: int = 3):
    question_lower = question.lower()

    # quick keyword filter
    filtered = [
        p for p in discourse_posts
        if any(kw in (p["title"] + p["content"]).lower() for kw in question_lower.split())
    ] or discourse_posts  # fallback to all if nothing passes filter

    # score with difflib
    scored = []
    for post in filtered:
        text = f"{post.get('title', '')} {post.get('content', '')}"
        score = difflib.SequenceMatcher(None, question_lower, text.lower()).ratio()
        scored.append((score, post))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_n]]

# ─────────────────────────────────────────────
# POST endpoint: answer questions
# ─────────────────────────────────────────────
@app.post("/")
def answer_question(query: Query):
    try:
        matches = find_relevant_posts(query.question)
        context = "\n\n".join(
            f"Title: {m['title']}\nContent: {m['content']}"
            for m in matches
        )

        prompt = (
            "You are a helpful TA. Use the following Discourse posts to answer the question.\n\n"
            f"Discourse Context:\n{context}\n\n"
            f"Question: {query.question}\nAnswer:"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You are a helpful TA. Answer based on context."},
                {"role": "user",   "content": prompt},
            ],
        )

        answer_text = response.choices[0].message.content.strip()
        links = [{"url": m.get("url", ""), "text": m.get("title", "")} for m in matches]

        return {"answer": answer_text, "links": links}

    except Exception as e:
        # Surface any error so you can see it in the response
        return {"error": str(e)}
