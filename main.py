from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
import os

app = FastAPI()

# Load your Gemini API key
genai.configure(api_key="AIzaSyCgREMwOvKlxBhDxC2gbNPZbyxdtFtnYyo")

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
