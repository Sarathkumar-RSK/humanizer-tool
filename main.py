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
    return {"message": "Smart Humanizer v6.0 - Waterfall Edition", "status": "online"}


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
# GROQ CALL HELPER
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


# ==========================================
# LEVEL 1: LIGHT HUMANIZE (Pure Python - FREE)
# ==========================================
def light_humanize(text):
    """No AI - just Python rules. Instant. 0 tokens."""
    
    # Replace AI buzzwords
    replacements = {
        'utilize': 'use', 'utilizes': 'uses', 'utilized': 'used',
        'facilitate': 'help', 'facilitates': 'helps',
        'leverage': 'use', 'leverages': 'uses',
        'implement': 'do', 'implements': 'does',
        'moreover': 'and', 'furthermore': 'also', 'additionally': 'also',
        'however': 'but', 'consequently': 'so', 'therefore': 'so',
        'nevertheless': 'still', 'nonetheless': 'still',
        'in conclusion,': '', 'in summary,': '',
        'it is important to note that': '',
        'it is worth noting that': '',
        'plays a crucial role': 'matters a lot',
        'plays a vital role': 'matters a lot',
        'delve into': 'look at', 'delves into': 'looks at',
        'navigate': 'handle', 'embark on': 'start',
        'tapestry': 'mix', 'realm': 'world',
        'landscape': 'scene', 'paradigm': 'model',
        'cutting-edge': 'new', 'robust': 'strong',
        'seamless': 'smooth', 'comprehensive': 'full',
        'innovative': 'new', 'revolutionize': 'change',
        'multifaceted': 'complex', 'underscore': 'show',
        'pivotal': 'key', 'profound': 'deep',
    }
    
    for old, new in replacements.items():
        text = re.sub(r'\b' + re.escape(old) + r'\b', new, text, flags=re.IGNORECASE)
    
    # Add contractions
    contractions = {
        'do not': "don't", 'does not': "doesn't", 'did not': "didn't",
        'cannot': "can't", 'can not': "can't",
        'will not': "won't", 'would not': "wouldn't",
        'should not': "shouldn't", 'could not': "couldn't",
        'is not': "isn't", 'are not': "aren't", 'was not': "wasn't",
        'were not': "weren't", 'has not': "hasn't", 'have not': "haven't",
        'it is': "it's", 'that is': "that's", 'there is': "there's",
        'you are': "you're", 'we are': "we're", 'they are': "they're",
        'I am': "I'm", 'I have': "I've", 'you have': "you've",
    }
    
    for old, new in contractions.items():
        text = re.sub(r'\b' + old + r'\b', new, text, flags=re.IGNORECASE)
    
    # Clean double spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ==========================================
# LEVEL 2: MEDIUM HUMANIZE (1 Groq call)
# ==========================================
def medium_humanize(text):
    """Single AI call. ~500 tokens."""
    system = "You make AI text sound natural and human."
    prompt = f"""Rewrite this to sound human. Use contractions, mix sentence lengths, add casual tone. Replace formal AI words with simple ones. Keep all facts. Return ONLY the rewritten text.

TEXT: {text}"""
    return call_groq(system, prompt, temp=1.0)


# ==========================================
# LEVEL 3: HEAVY HUMANIZE (3 Groq calls)
# ==========================================
def heavy_humanize(text):
    """Deep rewrite. ~1500 tokens."""
    
    # Pass 1: Restructure
    system1 = "You are an expert editor breaking robotic AI patterns."
    prompt1 = f"""Restructure to break AI patterns. Mix sentence lengths drastically. Replace AI words. Delete "in conclusion" type phrases. Keep all facts. Return ONLY the rewritten text.

TEXT: {text}"""
    stage1 = call_groq(system1, prompt1, temp=0.9)
    
    # Pass 2: Human voice
    system2 = "You are a casual blogger writing like talking to a friend."
    prompt2 = f"""Rewrite casually. Use contractions, fillers (honestly, basically, you know), rhetorical questions. Start sentences with And, But, So. Use em-dashes. Keep facts. Return ONLY the rewritten text.

TEXT: {stage1}"""
    stage2 = call_groq(system2, prompt2, temp=1.0)
    
    # Pass 3: Add imperfections
    system3 = "You add natural human imperfections."
    prompt3 = f"""Polish with imperfections. Add sentence fragments. Vary paragraphs. Avoid: delve, navigate, tapestry, realm, robust, seamless. Keep facts. Return ONLY the polished text.

TEXT: {stage2}"""
    stage3 = call_groq(system3, prompt3, temp=1.1)
    
    return stage3


# ==========================================
# 🌊 WATERFALL HUMANIZER (THE BRAIN!)
# Used by BOTH website AND n8n
# ==========================================
def waterfall_humanize(text, target_ai=15, max_loops=3):
    """
    Smart waterfall: Light → Medium → Heavy
    Stops as soon as target is reached.
    Returns BEST result if target not reached.
    """
    
    attempts = []
    
    # CHECK ORIGINAL SCORE FIRST
    original_score = detect_ai_score(text)
    best_text = text
    best_score = original_score
    best_method = "original"
    
    attempts.append({
        "level": 0,
        "method": "original",
        "ai_score": original_score
    })
    
    # If original is already good, return it!
    if original_score <= target_ai:
        return {
            "humanized": text,
            "final_ai_score": original_score,
            "original_ai_score": original_score,
            "human_score": 100 - original_score,
            "attempts": attempts,
            "total_attempts": 0,
            "best_method": "original",
            "target_reached": True,
            "tokens_used": "0 (no AI needed!)"
        }
    
    # LEVEL 1: LIGHT (Python rules - FREE)
    if max_loops >= 1:
        try:
            light_text = light_humanize(text)
            light_score = detect_ai_score(light_text)
            
            attempts.append({
                "level": 1,
                "method": "light (Python)",
                "ai_score": light_score
            })
            
            if light_score < best_score:
                best_score = light_score
                best_text = light_text
                best_method = "light (Python)"
            
            if light_score <= target_ai:
                return {
                    "humanized": best_text,
                    "final_ai_score": best_score,
                    "original_ai_score": original_score,
                    "human_score": 100 - best_score,
                    "attempts": attempts,
                    "total_attempts": 1,
                    "best_method": best_method,
                    "target_reached": True,
                    "tokens_used": "0 (Python only!)"
                }
        except Exception as e:
            print(f"Light failed: {e}")
    
    # LEVEL 2: MEDIUM (1 Groq call)
    if max_loops >= 2:
        try:
            medium_text = medium_humanize(best_text)
            medium_score = detect_ai_score(medium_text)
            
            attempts.append({
                "level": 2,
                "method": "medium (1 AI call)",
                "ai_score": medium_score
            })
            
            if medium_score < best_score:
                best_score = medium_score
                best_text = medium_text
                best_method = "medium (1 AI call)"
            
            if medium_score <= target_ai:
                return {
                    "humanized": best_text,
                    "final_ai_score": best_score,
                    "original_ai_score": original_score,
                    "human_score": 100 - best_score,
                    "attempts": attempts,
                    "total_attempts": 2,
                    "best_method": best_method,
                    "target_reached": True,
                    "tokens_used": "~500"
                }
        except Exception as e:
            print(f"Medium failed: {e}")
    
    # LEVEL 3: HEAVY (3 Groq calls)
    if max_loops >= 3:
        try:
            heavy_text = heavy_humanize(best_text)
            heavy_score = detect_ai_score(heavy_text)
            
            attempts.append({
                "level": 3,
                "method": "heavy (3 AI calls)",
                "ai_score": heavy_score
            })
            
            if heavy_score < best_score:
                best_score = heavy_score
                best_text = heavy_text
                best_method = "heavy (3 AI calls)"
        except Exception as e:
            print(f"Heavy failed: {e}")
    
    # Return BEST attempt
    return {
        "humanized": best_text,
        "final_ai_score": best_score,
        "original_ai_score": original_score,
        "human_score": 100 - best_score,
        "attempts": attempts,
        "total_attempts": len(attempts) - 1,
        "best_method": best_method,
        "target_reached": best_score <= target_ai,
        "tokens_used": "~2000"
    }


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
# WEBSITE ENDPOINT (No API key needed)
# ==========================================
@app.post("/smart-humanize")
def smart_humanize(data: SmartInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long. Max 5000 chars.")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short. Min 20 characters.")
    
    return waterfall_humanize(
        text=data.text,
        target_ai=data.target_ai,
        max_loops=data.max_loops
    )


# ==========================================
# N8N ENDPOINT (Needs API key)
# ==========================================
@app.post("/humanize")
def humanize_for_n8n(data: TextInput, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    
    result = waterfall_humanize(
        text=data.text,
        target_ai=15,
        max_loops=3
    )
    
    # Return in n8n-friendly format
    return {
        "content": result["humanized"],
        "text": result["humanized"],
        "humanized": result["humanized"],
        "original": data.text,
        "ai_score": result["final_ai_score"],
        "human_score": result["human_score"],
        "method_used": result["best_method"],
        "target_reached": result["target_reached"]
    }


# ==========================================
# PUBLIC HUMANIZE (Simple version)
# ==========================================
@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long. Max 5000 chars.")
    
    result = waterfall_humanize(text=data.text, target_ai=15, max_loops=3)
    
    return {
        "humanized": result["humanized"],
        "ai_score": result["final_ai_score"],
        "human_score": result["human_score"]
    }
