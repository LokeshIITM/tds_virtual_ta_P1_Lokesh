# Virtual Teaching Assistant (TDS Discourse Responder) 🤖📚

This is a FastAPI-based virtual assistant designed to answer student questions for the **Tools in Data Science (TDS)** course at IIT Madras, based on:

- TDS Discourse posts from **1 Jan – 14 Apr 2025**
- Course content as of **15 Apr 2025**

---

## 🔧 Features

- Accepts questions via a REST API
- Optional screenshot support (base64 encoded)
- Uses **Gemini (Google Generative AI)** to generate answers
- Can be updated to use other models (GPT, Claude, etc.)
- Scrapes Discourse posts and saves locally as `tds_discourse.json`

---

## 📦 API Usage

**Endpoint:**
