from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import difflib

app = FastAPI()

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        links = [{"url": m.get("url", ""), "text": m.get("title", "")} for m in matches]

        return {
            "answer": response.text.strip(),
            "links": links
        }

    except Exception as e:
        return {"error": str(e)}
