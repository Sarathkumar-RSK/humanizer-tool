from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os
import re
import requests

load_dotenv()
app = FastAPI()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

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
    return {"status": "online", "version": "Humanizer Pro v10.0 - Gemini Powered"}


# ==========================================
# PATTERN-BASED DETECTOR (Backup/Fallback)
# ==========================================
def detect_ai_pattern(text):
    score = 0
    text_lower = text.lower()
    word_count = len(text.split())

    if word_count < 20:
        return 50

    ai_words = [
        'moreover', 'furthermore', 'additionally', 'utilize', 'facilitate',
        'leverage', 'robust', 'seamless', 'comprehensive', 'innovative',
        'delve', 'navigate', 'tapestry', 'realm', 'landscape', 'paradigm',
        'in conclusion', 'in summary', 'it is important to note',
        'multifaceted', 'pivotal', 'profound', 'cutting-edge', 'it is worth noting',
        'notably', 'undoubtedly', 'certainly', 'as previously mentioned',
        'this ensures', 'this allows', 'this enables', 'plays a crucial role'
    ]

    ai_count = sum(1 for w in ai_words if w in text_lower)
    score += min(ai_count * 8, 40)

    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(sentences) > 3:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        var = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if var < 20:
            score += 15
        elif var < 40:
            score += 8

    contractions = ["don't", "can't", "won't", "it's", "i'm", "you're", "that's", "isn't", "aren't", "we're"]
    if not any(c in text_lower for c in contractions) and word_count > 50:
        score += 15

    # Check for no paragraph breaks (AI tends to write in single blocks)
    if '\n' not in text and word_count > 100:
        score += 10

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
# GEMINI HUMANIZER - LEVEL 1 (Standard Pass)
# ==========================================
def humanize_text_standard(text):
    prompt = f"""You are a master at making AI text completely undetectable by AI detectors like ZeroGPT, GPTZero, Turnitin, and QuillBot.

REWRITE the text below so it sounds 100% like a real human wrote it.

CRITICAL RULES - APPLY EVERY SINGLE ONE:

1. CONTRACTIONS EVERYWHERE: use don't, won't, can't, it's, that's, I'm, you're, we're, they're, isn't, aren't constantly
2. WILD sentence length variation: Mix 3-word fragments with 25+ word sentences randomly. Like this. Short. Then a really long one that goes on and on.
3. Personal fillers: use "honestly", "look", "I mean", "you know", "basically", "frankly", "actually", "tbh"
4. Start some sentences with: And, But, So, Now, Look, Well, Honestly
5. Use Em-dashes — like this — for natural asides
6. Add 1-2 rhetorical questions somewhere natural
7. DELETE these AI words and replace:
   - utilize → use
   - facilitate → help
   - leverage → use
   - moreover/furthermore → and/also
   - however → but
   - therefore/consequently → so
   - in conclusion → (just end naturally)
   - it is important to note → (delete entirely)
   - delve into → look at / dig into
   - navigate → handle / deal with
   - tapestry, realm, landscape, paradigm → replace with simple word
   - robust → strong / solid
   - seamless → smooth
   - comprehensive → full / complete
   - innovative → new / fresh
   - pivotal → key / important
   - multifaceted → complex
   - it is worth noting → (delete)
   - this ensures → this means
   - plays a crucial role → matters a lot / is key
8. Add sentence fragments randomly. Just like this. Works well.
9. Mix formal and casual tone naturally
10. Vary paragraph lengths — some 1 sentence, some 4-5 sentences
11. Add slight imperfections like "kinda", "gonna", "a lot" sparingly
12. Use "and" to start sentences sometimes — it's more natural

KEEP ALL FACTS AND MEANING INTACT. Only change HOW it's written.

Return ONLY the rewritten text. No explanations. No quotes.

TEXT TO REWRITE:
{text}"""

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=1.4,
            top_p=0.95,
            top_k=64,
            max_output_tokens=8192,
        )
    )
    return response.text.strip()


# ==========================================
# GEMINI HUMANIZER - LEVEL 2 (Aggressive Pass)
# ==========================================
def humanize_text_aggressive(text):
    prompt = f"""The text below still sounds like AI. You need to make it sound COMPLETELY human — like a real person typing casually.

This needs to FOOL ZeroGPT and GPTZero completely. Score must reach near 0% AI.

DO THIS:
- Restructure sentences completely — don't just swap words
- Add personal opinions or tiny anecdotes ("I've seen this happen a lot", "from what I know")
- Use MORE contractions than feels necessary
- Break grammar rules slightly — start with And, But, So
- Add thinking words: "I mean", "honestly", "look", "basically"  
- Make some sentences really short. Like one word short. Seriously.
- Then write a long rambling sentence that feels like a real person just typing out their thoughts without stopping
- Use dashes — like this — and (parentheses) for side thoughts
- Remove any remaining formal/academic language
- Add a rhetorical question if there isn't one already
- Use "a lot" instead of "many", "get" instead of "obtain", "show" instead of "demonstrate"
- Occasionally repeat an idea in different words like a human would
- Break into more paragraphs — shorter chunks feel more human

KEEP ALL FACTS. Return ONLY the rewritten text.

TEXT:
{text}"""

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=1.6,
            top_p=0.98,
            top_k=64,
            max_output_tokens=8192,
        )
    )
    return response.text.strip()


# ==========================================
# GEMINI HUMANIZER - LEVEL 3 (Nuclear Pass)
# ==========================================
def humanize_text_nuclear(text):
    prompt = f"""This text is still being detected as AI-written. You must completely transform it.

NUCLEAR HUMANIZATION — maximum effort:

COMPLETELY rewrite from scratch using the same facts/information but:
- Write like you're explaining to a friend in a message
- Use very casual but intelligent tone
- Add personal perspective: "honestly", "in my experience", "I've noticed"
- Make it conversational — like the person is talking, not writing an essay
- Short punchy sentences mixed with longer flowing ones
- No academic structure — no "firstly, secondly, finally"
- Use contractions for EVERY POSSIBLE WORD
- Add filler phrases naturally: "you know what I mean", "that kind of thing", "stuff like that"
- Break "rules" — start sentences with conjunctions, use fragments
- Use — dashes — and (parentheses) liberally
- Add 2-3 rhetorical questions
- Vary rhythm dramatically — fast then slow — punchy then flowing
- Replace any remaining formal words with simple everyday words
- Make it feel ALIVE and imperfect

FACTS MUST STAY THE SAME. Return ONLY the rewritten text. No intro, no explanation.

TEXT:
{text}"""

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=1.8,
            top_p=0.99,
            top_k=64,
            max_output_tokens=8192,
        )
    )
    return response.text.strip()


# ==========================================
# MASTER HUMANIZER - LOOPS UNTIL SCORE = 0-15%
# ==========================================
def humanize_until_zero(text, target_score=15, max_attempts=6):
    """
    Keeps humanizing until AI score drops to target (default 15% or below)
    Max 6 attempts to avoid infinite loop
    Uses escalating aggression levels
    """

    best_text = text
    best_score = detect_ai_real(text)
    original_score = best_score

    print(f"Starting score: {best_score}%")

    # If already below target, return as-is
    if best_score <= target_score:
        return best_text, best_score, original_score, 0

    attempt = 0

    while best_score > target_score and attempt < max_attempts:
        attempt += 1
        print(f"Attempt {attempt} — Current best score: {best_score}%")

        try:
            # Escalate aggression based on attempt number
            if attempt <= 2:
                # Level 1: Standard humanization
                candidate = humanize_text_standard(best_text)
            elif attempt <= 4:
                # Level 2: Aggressive humanization
                candidate = humanize_text_aggressive(best_text)
            else:
                # Level 3: Nuclear humanization
                candidate = humanize_text_nuclear(best_text)

            candidate_score = detect_ai_real(candidate)
            print(f"  → Candidate score: {candidate_score}%")

            # Always keep the best result
            if candidate_score < best_score:
                best_text = candidate
                best_score = candidate_score
                print(f"  ✓ New best: {best_score}%")

            # Stop if we hit target
            if best_score <= target_score:
                print(f"  🎯 Target reached: {best_score}%")
                break

        except Exception as e:
            print(f"  ✗ Attempt {attempt} failed: {e}")
            continue

    return best_text, best_score, original_score, attempt


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


# Website endpoint (public) - loops until score near zero
@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 chars)")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short (min 20 chars)")

    # Run the loop until score hits 0-15%
    humanized, final_score, original_score, attempts = humanize_until_zero(
        text=data.text,
        target_score=15,   # Aim for 15% or below
        max_attempts=6     # Max 6 tries
    )

    return {
        "humanized": humanized,
        "original_ai_score": original_score,
        "final_ai_score": final_score,
        "human_score": 100 - final_score,
        "improvement": original_score - final_score,
        "attempts_used": attempts,
        "target_reached": final_score <= 15
    }


# n8n endpoint (needs API key) - also loops until zero
@app.post("/humanize")
def humanize_for_n8n(data: TextInput, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    humanized, final_score, original_score, attempts = humanize_until_zero(
        text=data.text,
        target_score=15,
        max_attempts=6
    )

    return {
        "content": humanized,
        "text": humanized,
        "humanized": humanized,
        "ai_score": final_score,
        "human_score": 100 - final_score,
        "original_ai_score": original_score,
        "improvement": original_score - final_score,
        "attempts_used": attempts,
        "target_reached": final_score <= 15
    }


# Optional: Custom target score endpoint
@app.post("/humanize-custom/{target}")
def humanize_custom_target(target: int, data: TextInput, x_api_key: str = Header(None)):
    """Humanize with custom target score (0-50)"""
    verify_api_key(x_api_key)

    if target < 0 or target > 50:
        raise HTTPException(status_code=400, detail="Target must be between 0 and 50")
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 chars)")

    humanized, final_score, original_score, attempts = humanize_until_zero(
        text=data.text,
        target_score=target,
        max_attempts=8  # More attempts for custom targets
    )

    return {
        "content": humanized,
        "humanized": humanized,
        "ai_score": final_score,
        "human_score": 100 - final_score,
        "original_ai_score": original_score,
        "improvement": original_score - final_score,
        "attempts_used": attempts,
        "target_score": target,
        "target_reached": final_score <= target
    }
