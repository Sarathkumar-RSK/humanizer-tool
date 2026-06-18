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
    target_ai: int = 15
    max_loops: int = 3


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
    return {"message": "Smart Humanizer v7.0", "status": "online"}


def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def detect_ai_score(text):
    score = 0
    text_lower = text.lower()
    word_count = len(text.split())
    
    if word_count < 20:
        return 50
    
    ai_words = ['moreover', 'furthermore', 'additionally', 'consequently',
        'utilize', 'facilitate', 'leverage', 'implement', 'robust', 'seamless',
        'comprehensive', 'innovative', 'revolutionize', 'enhance', 'optimize',
        'streamline', 'delve', 'navigate', 'embark', 'tapestry', 'realm',
        'landscape', 'journey', 'paradigm', 'cutting-edge', 'in conclusion',
        'in summary', 'it is important to note', 'multifaceted', 'pivotal']
    
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
    c_count = sum(1 for c in contractions if c in text_lower)
    if c_count == 0 and word_count > 50: score += 15
    
    if text.count(',') / max(word_count, 1) > 0.08: score += 10
    
    personal = ['i think', 'honestly', 'basically', 'you know', 'look,', 'so,']
    if not any(p in text_lower for p in personal) and word_count > 100: score += 10
    
    return min(score, 100)


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


# ATTEMPT 1: LIGHT (Python - 0 tokens)
def light_humanize(text):
    replacements = {
        'utilize': 'use', 'facilitate': 'help', 'leverage': 'use',
        'implement': 'do', 'moreover': 'and', 'furthermore': 'also',
        'additionally': 'also', 'however': 'but', 'consequently': 'so',
        'therefore': 'so', 'in conclusion,': '', 'in summary,': '',
        'it is important to note that': '', 'delve into': 'look at',
        'navigate': 'handle', 'tapestry': 'mix', 'realm': 'world',
        'landscape': 'scene', 'cutting-edge': 'new', 'robust': 'strong',
        'seamless': 'smooth', 'comprehensive': 'full', 'innovative': 'new',
        'multifaceted': 'complex', 'pivotal': 'key'
    }
    for old, new in replacements.items():
        text = re.sub(r'\b' + re.escape(old) + r'\b', new, text, flags=re.IGNORECASE)
    
    contractions = {
        'do not': "don't", 'cannot': "can't", 'will not': "won't",
        'is not': "isn't", 'are not': "aren't", 'it is': "it's",
        'that is': "that's", 'you are': "you're", 'I am': "I'm"
    }
    for old, new in contractions.items():
        text = re.sub(r'\b' + old + r'\b', new, text, flags=re.IGNORECASE)
    
    return re.sub(r'\s+', ' ', text).strip()


# ATTEMPT 2: MEDIUM (1 Groq call)
def medium_humanize(text):
    system = "You make AI text sound natural and human."
    prompt = f"""Rewrite this to sound human. Use contractions, mix sentence lengths, add casual tone. Replace formal words with simple ones. Keep all facts. Return ONLY the rewritten text.

TEXT: {text}"""
    return call_groq(system, prompt, temp=1.0)


# ATTEMPT 3: HEAVY (3 Groq calls)
def heavy_humanize(text):
    s1 = "You are an expert editor breaking AI patterns."
    p1 = f"Restructure to break AI patterns. Mix sentence lengths. Keep facts. Return ONLY rewritten text.\n\nTEXT: {text}"
    stage1 = call_groq(s1, p1, temp=0.9)
    
    s2 = "You are a casual blogger."
    p2 = f"Rewrite casually with contractions, fillers (honestly, basically), questions. Keep facts. Return ONLY text.\n\nTEXT: {stage1}"
    stage2 = call_groq(s2, p2, temp=1.0)
    
    s3 = "You add human imperfections."
    p3 = f"Polish with imperfections, sentence fragments. Avoid: delve, tapestry, realm, robust. Keep facts. Return ONLY text.\n\nTEXT: {stage2}"
    return call_groq(s3, p3, temp=1.1)


# 🌊 WATERFALL HUMANIZER (Clean 3 attempts only!)
def waterfall_humanize(text, target_ai=15, max_loops=3):
    original_score = detect_ai_score(text)
    attempts = []
    best_text = text
    best_score = original_score
    best_method = "none"
    
    # ATTEMPT 1: LIGHT
    try:
        result = light_humanize(text)
        score = detect_ai_score(result)
        attempts.append({"attempt": 1, "method": "Light (Python)", "ai_score": score})
        if score < best_score:
            best_score, best_text, best_method = score, result, "Light (Python)"
        if score <= target_ai:
            return _build_result(text, best_text, best_score, best_method, original_score, attempts, True)
    except Exception as e:
        attempts.append({"attempt": 1, "method": "Light (Python)", "ai_score": "error"})
    
    # ATTEMPT 2: MEDIUM
    try:
        result = medium_humanize(best_text)
        score = detect_ai_score(result)
        attempts.append({"attempt": 2, "method": "Medium (1 AI call)", "ai_score": score})
        if score < best_score:
            best_score, best_text, best_method = score, result, "Medium (1 AI call)"
        if score <= target_ai:
            return _build_result(text, best_text, best_score, best_method, original_score, attempts, True)
    except Exception as e:
        attempts.append({"attempt": 2, "method": "Medium (1 AI call)", "ai_score": "error"})
    
    # ATTEMPT 3: HEAVY
    try:
        result = heavy_humanize(best_text)
        score = detect_ai_score(result)
        attempts.append({"attempt": 3, "method": "Heavy (3 AI calls)", "ai_score": score})
        if score < best_score:
            best_score, best_text, best_method = score, result, "Heavy (3 AI calls)"
    except Exception as e:
        attempts.append({"attempt": 3, "method": "Heavy (3 AI calls)", "ai_score": "error"})
    
    return _build_result(text, best_text, best_score, best_method, original_score, attempts, best_score <= target_ai)


def _build_result(original, final_text, final_score, method, orig_score, attempts, target_reached):
    return {
        "humanized": final_text,
        "final_ai_score": final_score,
        "original_ai_score": orig_score,
        "human_score": 100 - final_score,
        "attempts": attempts,
        "total_attempts": len(attempts),
        "best_method": method,
        "target_reached": target_reached
    }


@app.post("/detect")
def detect(data: TextInput):
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short.")
    score = detect_ai_score(data.text)
    return {"ai_score": score, "human_score": 100 - score,
            "verdict": "AI Generated" if score > 60 else "Likely Human" if score > 30 else "Human Written"}


@app.post("/smart-humanize")
def smart_humanize(data: SmartInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long. Max 5000 chars.")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short. Min 20 chars.")
    return waterfall_humanize(data.text, data.target_ai, data.max_loops)


@app.post("/humanize")
def humanize_for_n8n(data: TextInput, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    result = waterfall_humanize(data.text, 15, 3)
    return {
        "content": result["humanized"],
        "text": result["humanized"],
        "humanized": result["humanized"],
        "original": data.text,
        "ai_score": result["final_ai_score"],
        "human_score": result["human_score"]
    }


@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long.")
    result = waterfall_humanize(data.text, 15, 3)
    return {"humanized": result["humanized"], "ai_score": result["final_ai_score"],
            "human_score": result["human_score"]}
