from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
import re
import requests

load_dotenv()
app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MY_SECRET_KEY = os.getenv("MY_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"


class TextInput(BaseModel):
    text: str


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
    return {"status": "online", "version": "Humanizer Pro v12.0 - SUPER AGGRESSIVE"}


# ==========================================
# AI DETECTOR
# ==========================================
def detect_ai_real(text):
    try:
        response = requests.post(
            'https://api.zerogpt.com/api/detect/detectText',
            json={'input_text': text},
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            score = round(data.get('data', {}).get('fakePercentage', 0))
            print(f"  AI Score: {score}%")
            return score
    except Exception as e:
        print(f"  Detector error: {e}")
    return 50


# ==========================================
# GEMINI CALL
# ==========================================
def call_gemini(prompt: str, temperature: float = 1.5) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.98,
            top_k=64,
            max_output_tokens=8192,
        )
    )
    return response.text.strip()


# ==========================================
# SUPER AGGRESSIVE HUMANIZER
# ==========================================
def humanize_super(text, attempt=1):
    
    if attempt == 1:
        style = "casual blog writer"
        instruction = "Rewrite naturally with personal voice"
    elif attempt == 2:
        style = "experienced journalist writing for a magazine"
        instruction = "Completely restructure - new sentence flow, casual professional tone"
    elif attempt == 3:
        style = "Reddit user explaining to friends"
        instruction = "Make it super conversational, like talking out loud"
    elif attempt == 4:
        style = "expert sharing personal experience"
        instruction = "Add anecdotes, opinions, personal touches everywhere"
    else:
        style = "natural human writer - completely from scratch"
        instruction = "REWRITE FROM SCRATCH. Keep facts only. Change EVERYTHING else."
    
    prompt = f"""You are a {style}. {instruction}.

CRITICAL: This text is being detected as AI-generated. You MUST make it 100% undetectable.

RULES (FOLLOW EVERY SINGLE ONE):

1. COMPLETELY restructure every sentence - don't just swap words
2. Mix sentence lengths drastically:
   - Some 3-5 word punches. Like this.
   - Then long flowing sentences that connect multiple ideas with natural rhythm and feel exactly like how a real person would explain something in writing
3. Use contractions EVERYWHERE: don't, won't, it's, that's, I've, we're, you'll, they'd
4. Add personal voice phrases:
   - "honestly"
   - "look"  
   - "here's the thing"
   - "what I've noticed"
   - "in my experience"
   - "the way I see it"
5. Start sentences with And, But, So, Now, Look
6. Use em-dashes — like this — and (parentheses) for asides
7. Add 2-3 rhetorical questions
8. NEVER use these AI-tell words:
   ❌ Furthermore, Moreover, Additionally, However, Therefore, Consequently
   ❌ Utilize, Facilitate, Leverage, Robust, Seamless, Comprehensive
   ❌ Delve into, Navigate, Tapestry, Realm, Landscape, Paradigm
   ❌ "It is important to note", "In conclusion", "It is worth noting"
   ❌ "Plays a crucial role", "This ensures", "This allows"
9. Replace with simple words:
   - utilize → use
   - moreover → also
   - however → but
   - therefore → so
   - in conclusion → (just end)
10. Vary paragraph lengths - some 1 sentence, some 4-5 sentences
11. Add slight imperfections that real humans make
12. Use specific examples instead of generic statements
13. Add transitions like: "anyway", "moving on", "now here's where it gets interesting"

KEEP ALL FACTS, NUMBERS, AND KEY INFORMATION INTACT.
ONLY change HOW it's written, not WHAT it says.

Return ONLY the rewritten text. No intro, no explanations, no markdown formatting like ```.

TEXT TO COMPLETELY REWRITE:
{text}"""

    return call_gemini(prompt, temperature=1.4 + (attempt * 0.1))


# ==========================================
# MASTER LOOP - VERY AGGRESSIVE
# ==========================================
def humanize_until_zero(text, target_score=15, max_attempts=8):
    original_score = detect_ai_real(text)
    print(f"📊 Original: {original_score}%")
    
    # If already low, still try to improve
    if original_score <= 5:
        print(f"✅ Already excellent ({original_score}%)")
        return text, original_score, original_score, 0
    
    best_text = text
    best_score = original_score
    attempt = 0
    
    while best_score > target_score and attempt < max_attempts:
        attempt += 1
        print(f"🔄 Attempt {attempt}/{max_attempts} — Best: {best_score}%")
        
        try:
            # Always work on BEST text so far (cumulative improvement)
            candidate = humanize_super(best_text, attempt)
            candidate_score = detect_ai_real(candidate)
            print(f"  → Result: {candidate_score}%")
            
            if candidate_score < best_score:
                best_text = candidate
                best_score = candidate_score
                print(f"  ✓ IMPROVED to {best_score}%")
            else:
                print(f"  ✗ Worse, keeping previous ({best_score}%)")
                # If no improvement, try humanizing the original again
                if attempt > 2:
                    candidate2 = humanize_super(text, attempt)
                    score2 = detect_ai_real(candidate2)
                    if score2 < best_score:
                        best_text = candidate2
                        best_score = score2
                        print(f"  ✓ Fresh attempt better: {best_score}%")
            
            if best_score <= target_score:
                print(f"  🎯 TARGET REACHED!")
                break
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    print(f"🏁 Final: {best_score}% after {attempt} attempts")
    return best_text, best_score, original_score, attempt


# ==========================================
# ENDPOINTS
# ==========================================
@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 8000:
        raise HTTPException(status_code=400, detail="Text too long (max 8000)")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short (min 20)")
    
    humanized, final_score, original_score, attempts = humanize_until_zero(
        text=data.text,
        target_score=15,
        max_attempts=8
    )
    
    return {
        "humanized": humanized,
        "content": humanized,
        "text": humanized,
        "original_ai_score": original_score,
        "final_ai_score": final_score,
        "human_score": 100 - final_score,
        "improvement": original_score - final_score,
        "attempts_used": attempts,
        "target_reached": final_score <= 15,
        "success": final_score <= 15
    }


@app.post("/humanize")
def humanize_for_n8n(data: TextInput, x_api_key: str = Header(None)):
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if len(data.text) > 8000:
        raise HTTPException(status_code=400, detail="Text too long")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short")
    
    humanized, final_score, original_score, attempts = humanize_until_zero(
        text=data.text,
        target_score=15,
        max_attempts=8
    )
    
    return {
        "humanized": humanized,
        "content": humanized,
        "text": humanized,
        "ai_score": final_score,
        "original_ai_score": original_score,
        "human_score": 100 - final_score,
        "improvement": original_score - final_score,
        "attempts_used": attempts,
        "target_reached": final_score <= 15,
        "success": final_score <= 15
    }
