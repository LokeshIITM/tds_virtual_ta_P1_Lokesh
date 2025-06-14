from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import difflib

app = FastAPI()

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load Discourse data at startup
with open("tds_discourse.json", "r", encoding="utf-8") as f:
    discourse_posts = json.load(f)

# Pydantic model
class Query(BaseModel):
    question: str
    image: Optional[str] = None

def find_relevant_posts(question: str, top_n: int = 3):
    """
    Find top N most similar discourse posts to the question
    using basic string similarity.
    """
    scored = []
    for post in discourse_posts:
        title = post.get("title", "")
        content = post.get("content", "")
        text = f"{title} {content}"
        score = difflib.SequenceMatcher(None, question.lower(), text.lower()).ratio()
        scored.append((score, post))

    # top_posts = sorted(scored, reverse=True)[:top_n]
    top_posts = sorted(scored, key=lambda x: x[0], reverse=True)[:top_n]

    return [p for _, p in top_posts]

@app.post("/")
def answer_question(query: Query):
    try:
        # Find related Discourse posts
        matches = find_relevant_posts(query.question)
        context = "\n\n".join([f"Title: {m['title']}\nContent: {m['content']}" for m in matches])
        prompt = f"""You are a helpful TA. Use the following Discourse posts to answer the question.

Discourse Context:
{context}

Question: {query.question}
Answer:"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Format links
        links = [{"url": m.get("url", ""), "text": m.get("title", "")} for m in matches]

        return {
            "answer": response.text.strip(),
            "links": links
        }

    except Exception as e:
        return {"error": str(e)}
