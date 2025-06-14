from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os

app = FastAPI()

# Load .env and configure Gemini key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define request structure
class Query(BaseModel):
    question: str
    image: Optional[str] = None

@app.post("/")
def answer_question(query: Query):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(query.question)

        return {
            "answer": response.text.strip(),
            "links": [
                {"url": "https://discourse.onlinedegree.iitm.ac.in", "text": "Reference Discourse"}
            ]
        }

    except Exception as e:
        return {"error": str(e)}
