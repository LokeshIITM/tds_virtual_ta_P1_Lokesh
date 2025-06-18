from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import openai
import os
import json
import difflib
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def read_root():
    return JSONResponse(content={"message": "TDS Virtual TA is live!"})

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("AIPROXY_TOKEN")
openai.base_url = "https://aiproxy.sanand.workers.dev/openai"

# Load the scraped discourse data
with open("tds_discourse.json", "r", encoding="utf-8") as f:
    discourse_posts = json.load(f)

# Pydantic model for the request
class Query(BaseModel):
    question: str
    image: Optional[str] = None

# Search for relevant posts using difflib
def find_relevant_posts(question: str, top_n: int = 3):
    question_lower = question.lower()

    # Filter posts that have at least one question word
    filtered = [p for p in discourse_posts if any(
        kw in p["title"].lower() or kw in p["content"].lower()
        for kw in question_lower.split()
    )]

    scored = []
    for post in filtered:
        title = post.get("title", "")
        content = post.get("content", "")
        text = f"{title} {content}"
        score = difflib.SequenceMatcher(None, question_lower, text.lower()).ratio()
        scored.append((score, post))

    # If no filtered matches, fall back to full list
    if not scored:
        for post in discourse_posts:
            title = post.get("title", "")
            content = post.get("content", "")
            text = f"{title} {content}"
            score = difflib.SequenceMatcher(None, question_lower, text.lower()).ratio()
            scored.append((score, post))

    return [pair[1] for pair in sorted(scored, key=lambda x: x[0], reverse=True)[:top_n]]

# API endpoint to answer questions
@app.post("/")
def answer_question(query: Query):
    try:
        matches = find_relevant_posts(query.question)
        context = "\n\n".join([f"Title: {m['title']}\nContent: {m['content']}" for m in matches])
        prompt = f"""You are a helpful TA. Use the following Discourse posts to answer the question.

Discourse Context:
{context}

Question: {query.question}
Answer:"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You are a helpful TA. Answer based on context."},
                {"role": "user", "content": prompt}
            ]
        )

        answer_text = response['choices'][0]['message']['content'].strip()
        links = [{"url": m.get("url", ""), "text": m.get("title", "")} for m in matches]

        return {
            "answer": answer_text,
            "links": links
        }

    except Exception as e:
        return {"error": str(e)}
