from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.responses import JSONResponse
import os
import json
import difflib

app = FastAPI()

@app.get("/")
def read_root():
    return JSONResponse(content={"message": "TDS Virtual TA is live!"})

# Load environment variables
load_dotenv()

client = OpenAI(
    api_key=os.getenv("AIPROXY_TOKEN"),
    base_url="https://aiproxy.sanand.workers.dev/openai"
)


# Load the scraped discourse data
with open("tds_discourse.json", "r", encoding="utf-8") as f:
    discourse_posts = json.load(f)

class Query(BaseModel):
    question: str
    image: Optional[str] = None

def find_relevant_posts(question: str, top_n: int = 3):
    question_lower = question.lower()
    filtered = [p for p in discourse_posts if any(
        kw in (p["title"] + p["content"]).lower()
        for kw in question_lower.split()
    )] or discourse_posts

    scored = []
    for post in filtered:
        text = f"{post.get('title', '')} {post.get('content', '')}"
        score = difflib.SequenceMatcher(None, question_lower, text.lower()).ratio()
        scored.append((score, post))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_n]]

@app.post("/")
def answer_question(query: Query):
    try:
        matches = find_relevant_posts(query.question)
        context = "\n\n".join(
            f"Title: {m['title']}\nContent: {m['content']}" for m in matches
        )

        prompt = (
            "You are a helpful TA. Use the following Discourse posts to answer the question.\n\n"
            f"Discourse Context:\n{context}\n\n"
            f"Question: {query.question}\nAnswer:"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful TA. Answer based on context."},
                {"role": "user", "content": prompt}
            ]
        )


        answer_text = response.choices[0].message.content.strip()
        links = [{"url": m.get("url", ""), "text": m.get("title", "")} for m in matches]

        return {
            "answer": answer_text,
            "links": links
        }

    except Exception as e:
        return {"error": str(e)}
