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


class SmartInput(BaseModel):
    text: str
    target_ai: int = 20
    max_loops: int = 8


# ==========================================
# WEBSITE PAGES
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
    return {"message": "Smart Humanizer v5.0 is running", "status": "online"}


# ==========================================
# SECURITY
# ==========================================
def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ==========================================
# AI DETECTOR
# ==========================================
def detect_ai_score(text):
    score = 0
    text_lower = text.lower()
    word_count = len(text.split())
    
    if word_count < 20:
        return 50
    
    ai_words = [
        'moreover', 'furthermore', 'additionally', 'consequently',
        'utilize', 'facilitate', 'leverage', 'implement',
        'robust', 'seamless', 'comprehensive', 'innovative',
        'revolutionize', 'enhance', 'optimize', 'streamline',
        'delve', 'navigate', 'embark', 'tapestry', 'realm',
        'landscape', 'journey', 'paradigm', 'cutting-edge',
        'in conclusion', 'in summary', 'it is important to note',
        'it is worth noting', 'plays a crucial role', 'plays a vital role',
        'multifaceted', 'underscore', 'pivotal', 'profound'
    ]
    
    ai_word_count = sum(1 for word in ai_words if word in text_lower)
    score += min(ai_word_count * 8, 40)
    
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) > 3:
        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        if variance < 20:
            score += 15
        elif variance < 40:
            score += 8
    
    contractions = ["don't", "can't", "won't", "it's", "i'm", "you're", 
                    "we're", "they're", "i've", "you've", "that's", "what's"]
    contraction_count = sum(1 for c in contractions if c in text_lower)
    
    if contraction_count == 0 and word_count > 50:
        score += 15
    elif contraction_count < 2 and word_count > 100:
        score += 8
    
    if text.count(',') / max(word_count, 1) > 0.08:
        score += 10
    
    personal_words = ['i think', 'i believe', 'in my experience', 
                      'personally', 'honestly', 'frankly', 'look,',
                      'so,', 'well,', 'you know']
    personal_count = sum(1 for p in personal_words if p in text_lower)
    
    if personal_count == 0 and word_count > 100:
        score += 10
    
    return min(score, 100)


# ==========================================
# HUMANIZER ENGINE
# ==========================================
def call_groq(system_msg, user_msg, temp=1.0):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=temp,
        top_p=0.95,
    )
    return response.choices[0].message.content


def pass_1_restructure(text):
    system = "You are an expert editor who breaks robotic AI writing patterns."
    prompt = f"""Restructure this text to break AI patterns. Mix sentence lengths drastically. Replace AI words: utilize to use, facilitate to help, leverage to use, moreover/furthermore to and, however to but. Delete "in conclusion" and "it is important to note". Keep all facts. Return ONLY the rewritten text.

TEXT: {text}"""
    return call_groq(system, prompt, temp=0.9)


def pass_2_human_voice(text):
    system = "You are a tired blogger writing casually like talking to a friend."
    prompt = f"""Rewrite in casual conversational voice. Use contractions (don't, can't, it's). Add fillers (honestly, look, basically, you know). Use rhetorical questions. Start sentences with And, But, So. Use em-dashes. Keep all facts. Return ONLY the rewritten text.

TEXT: {text}"""
    return call_groq(system, prompt, temp=1.0)


def pass_3_imperfections(text):
    system = "You add natural human imperfections to bypass AI detectors."
    prompt = f"""Polish with human imperfections. Add sentence fragments. Vary paragraph lengths. Avoid AI words: delve, navigate, embark, tapestry, realm, landscape, robust, seamless, comprehensive, innovative. Keep all facts. Return ONLY the polished text.

TEXT: {text}"""
    return call_groq(system, prompt, temp=1.1)


def humanize_text(text):
    stage1 = pass_1_restructure(text)
    stage2 = pass_2_human_voice(stage1)
    stage3 = pass_3_imperfections(stage2)
    return stage3


# ==========================================
# DETECTION ENDPOINT
# ==========================================
@app.post("/detect")
def detect(data: TextInput):
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short. Need at least 20 characters.")
    
    ai_score = detect_ai_score(data.text)
    
    return {
        "ai_score": ai_score,
        "human_score": 100 - ai_score,
        "verdict": "AI Generated" if ai_score > 60 else "Likely Human" if ai_score > 30 else "Human Written"
    }


# ==========================================
# REGULAR HUMANIZE (for n8n - needs API key)
# ==========================================
@app.post("/humanize")
def humanize(data: TextInput, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    result = humanize_text(data.text)
    return {
        "content": result,
        "text": result,
        "original": data.text,
        "humanized": result
    }


# ==========================================
# PUBLIC HUMANIZE
# ==========================================
@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long. Max 5000 chars.")
    
    result = humanize_text(data.text)
    ai_score = detect_ai_score(result)
    
    return {
        "humanized": result,
        "ai_score": ai_score,
        "human_score": 100 - ai_score
    }


# ==========================================
# SMART HUMANIZE (Auto-loop with BEST tracking)
# ==========================================
@app.post("/smart-humanize")
def smart_humanize(data: SmartInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long. Max 5000 chars.")
    
    original_score = detect_ai_score(data.text)
    current_text = data.text
    attempts = []
    best_text = data.text
    best_score = original_score
    best_attempt_num = 0
    
    for attempt_num in range(1, data.max_loops + 1):
        current_text = humanize_text(current_text)
        current_score = detect_ai_score(current_text)
        
        attempts.append({
            "attempt": attempt_num,
            "ai_score": current_score
        })
        
        if current_score < best_score:
            best_score = current_score
            best_text = current_text
            best_attempt_num = attempt_num
        
        if current_score <= data.target_ai:
            break
    
    return {
        "original_text": data.text,
        "humanized": best_text,
        "original_ai_score": original_score,
        "final_ai_score": best_score,
        "human_score": 100 - best_score,
        "attempts": attempts,
        "total_attempts": len(attempts),
        "best_attempt": best_attempt_num,
        "target_reached": best_score <= data.target_ai
    }
