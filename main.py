from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
import re
import requests

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
    return {"status": "online", "version": "Humanizer Pro v9.0 - Real Detector"}


# ==========================================
# PATTERN-BASED DETECTOR (Backup/Fallback)
# ==========================================
def detect_ai_pattern(text):
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
# REAL AI DETECTOR (ZeroGPT API + Pattern Hybrid)
# ==========================================
def detect_ai_real(text):
    """Uses ZeroGPT (real ML detector) + pattern-based for accuracy"""
    
    pattern_score = detect_ai_pattern(text)
    
    try:
        response = requests.post(
            'https://api.zerogpt.com/api/detect/detectText',
            json={'input_text': text},
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            zerogpt_score = round(data.get('data', {}).get('fakePercentage', 0))
            # Weighted average: 70% real detector + 30% pattern
            final_score = round((zerogpt_score * 0.7) + (pattern_score * 0.3))
            return final_score
        else:
            return pattern_score
            
    except Exception as e:
        print(f"ZeroGPT API failed: {e}")
        return pattern_score


# ==========================================
# POWERFUL HUMANIZER (Optimized for low AI score)
# ==========================================
def humanize_text(text):
    system_msg = """You are a master at making AI text completely undetectable. You break every robotic pattern AI uses."""
    
    user_msg = f"""REWRITE the text below to BYPASS AI detectors (ZeroGPT, QuillBot, GPTZero, Turnitin).

CRITICAL RULES - APPLY ALL:

1. CONTRACTIONS EVERYWHERE: don't, won't, can't, it's, that's, I'm, you're, we're, they're, isn't, aren't
2. WILD sentence length variation: Mix 3-word fragments with 25+ word sentences. Like this.
3. Personal fillers: "honestly", "look", "I mean", "you know", "basically", "frankly"
4. Start sentences with: And, But, So, Now, Look, Well
5. Em-dashes — used naturally — for asides
6. Add 1-2 rhetorical questions
7. DELETE these AI words completely:
   - utilize → use
   - facilitate → help  
   - leverage → use
   - moreover/furthermore → and/also
   - however → but
   - therefore/consequently → so
   - in conclusion → (delete)
   - it is important to note → (delete)
   - delve into → look at
   - navigate → handle
   - tapestry, realm, landscape, paradigm → (find simple word)
   - robust → strong
   - seamless → smooth
   - comprehensive → full
   - innovative → new
8. Add sentence fragments. Like this. Or this one.
9. Mix formal and casual tone
10. Use occasional typos-like casualness ("kinda", "gonna" sparingly)

KEEP ALL FACTS AND MEANING. Only change HOW it's written.

Return ONLY the rewritten text. No explanations. No quotes around it.

ORIGINAL TEXT:
{text}"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=1.2,
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

# Detect AI score only
@app.post("/detect")
def detect(data: TextInput):
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short (min 20 chars)")
    
    score = detect_ai_real(data.text)
    
    return {
        "ai_score": score,
        "human_score": 100 - score,
        "verdict": "AI Generated" if score > 60 else "Likely Human" if score > 30 else "Human Written"
    }


# Website endpoint (public) - with retry if AI score too high
@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 chars)")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short (min 20 chars)")
    
    # Get original score
    original_score = detect_ai_real(data.text)
    
    # First humanization attempt
    humanized = humanize_text(data.text)
    final_score = detect_ai_real(humanized)
    
    # If still too high (>30%), try ONE more pass on humanized text
    if final_score > 30:
        try:
            humanized_v2 = humanize_text(humanized)
            score_v2 = detect_ai_real(humanized_v2)
            # Keep the better one
            if score_v2 < final_score:
                humanized = humanized_v2
                final_score = score_v2
        except Exception as e:
            print(f"Second pass failed: {e}")
    
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
    final_score = detect_ai_real(humanized)
    
    # Second pass if needed
    if final_score > 30:
        try:
            humanized_v2 = humanize_text(humanized)
            score_v2 = detect_ai_real(humanized_v2)
            if score_v2 < final_score:
                humanized = humanized_v2
                final_score = score_v2
        except:
            pass
    
    return {
        "content": humanized,
        "text": humanized,
        "humanized": humanized,
        "ai_score": final_score,
        "human_score": 100 - final_score
    }
