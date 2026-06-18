from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
import re

load_dotenv()
app = FastAPI()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MY_SECRET_KEY = os.getenv("MY_API_KEY")


class TextInput(BaseModel):
    text: str


# ==========================================
# SERVE WEBSITE
# ==========================================
@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/style.css")
def get_css():
    return FileResponse("style.css", media_type="text/css")

@app.get("/script.js")
def get_js():
    return FileResponse("script.js", media_type="application/javascript")

@app.get("/status")
def status():
    return {"status": "online", "version": "Humanizer Pro v8.0"}


# ==========================================
# AI DETECTOR (Pattern-based, free)
# ==========================================
def detect_ai_score(text):
    score = 0
    text_lower = text.lower()
    word_count = len(text.split())
    
    if word_count < 20:
        return 50
    
    ai_words = ['moreover', 'furthermore', 'additionally', 'utilize', 'facilitate',
                'leverage', 'robust', 'seamless', 'comprehensive', 'innovative',
                'delve', 'navigate', 'tapestry', 'realm', 'landscape', 'paradigm',
                'in conclusion', 'in summary', 'it is important to note',
                'multifaceted', 'pivotal', 'profound', 'cutting-edge']
    
    ai_count = sum(1 for w in ai_words if w in text_lower)
    score += min(ai_count * 8, 40)
    
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(sentences) > 3:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        var = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if var < 20: score += 15
        elif var < 40: score += 8
    
    contractions = ["don't", "can't", "won't", "it's", "i'm", "you're", "that's"]
    if not any(c in text_lower for c in contractions) and word_count > 50:
        score += 15
    
    return min(score, 100)


# ==========================================
# HUMANIZER (Simple - 1 Groq call)
# ==========================================
def humanize_text(text):
    system_msg = "You are an expert at making AI text sound 100% human."
    
    user_msg = f"""Rewrite the text below to sound completely human-written. Apply ALL these changes:

1. Use contractions (don't, can't, it's, I'm, you're)
2. Mix sentence lengths (some short, some long, some fragments)
3. Add casual fillers (honestly, basically, look, you know)
4. Replace AI buzzwords:
   - utilize → use
   - facilitate → help
   - leverage → use
   - moreover/furthermore → and
   - however → but
5. Delete phrases like "in conclusion", "it is important to note", "delve into"
6. Start some sentences with And, But, So
7. Add a rhetorical question or two
8. Use em-dashes naturally
9. Keep ALL facts and meaning intact

Return ONLY the rewritten text. No explanations.

TEXT TO REWRITE:
{text}"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=1.0,
        top_p=0.95,
    )
    return response.choices[0].message.content.strip()


# ==========================================
# SECURITY (for n8n)
# ==========================================
def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ==========================================
# ENDPOINTS
# ==========================================

# Just detect AI score
@app.post("/detect")
def detect(data: TextInput):
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short (min 20 chars)")
    score = detect_ai_score(data.text)
    return {
        "ai_score": score,
        "human_score": 100 - score,
        "verdict": "AI Generated" if score > 60 else "Likely Human" if score > 30 else "Human Written"
    }


# Website endpoint (public)
@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 chars)")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short (min 20 chars)")
    
    original_score = detect_ai_score(data.text)
    humanized = humanize_text(data.text)
    final_score = detect_ai_score(humanized)
    
    return {
        "humanized": humanized,
        "original_ai_score": original_score,
        "final_ai_score": final_score,
        "human_score": 100 - final_score,
        "improvement": original_score - final_score
    }


# n8n endpoint (needs API key)
@app.post("/humanize")
def humanize_for_n8n(data: TextInput, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    
    humanized = humanize_text(data.text)
    final_score = detect_ai_score(humanized)
    
    return {
        "content": humanized,
        "text": humanized,
        "humanized": humanized,
        "ai_score": final_score,
        "human_score": 100 - final_score
    }
