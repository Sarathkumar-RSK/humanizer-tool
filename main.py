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

# Configure new Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MY_SECRET_KEY = os.getenv("MY_API_KEY")

# ==========================================
# CHECK AVAILABLE MODELS (run once to debug)
# ==========================================
# Uncomment below to see all available models in your logs
# for m in client.models.list():
#     print(m.name)

GEMINI_MODEL = "gemini-2.0-flash"


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
    return {
        "status": "online",
        "version": "Humanizer Pro v11.0 - Gemini 2.0 Flash",
        "model": GEMINI_MODEL
    }

@app.get("/models")
def list_models():
    """Debug endpoint — see all available models"""
    try:
        models = [m.name for m in client.models.list()]
        return {"models": models}
    except Exception as e:
        return {"error": str(e)}


# ==========================================
# PATTERN-BASED DETECTOR (Fallback)
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
        'multifaceted', 'pivotal', 'profound', 'cutting-edge',
        'it is worth noting', 'notably', 'undoubtedly', 'certainly',
        'as previously mentioned', 'this ensures', 'this allows',
        'this enables', 'plays a crucial role'
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

    contractions = [
        "don't", "can't", "won't", "it's", "i'm",
        "you're", "that's", "isn't", "aren't", "we're"
    ]
    if not any(c in text_lower for c in contractions) and word_count > 50:
        score += 15

    if '\n' not in text and word_count > 100:
        score += 10

    return min(score, 100)


# ==========================================
# REAL AI DETECTOR (ZeroGPT + Pattern Hybrid)
# ==========================================
def detect_ai_real(text):
    pattern_score = detect_ai_pattern(text)

    try:
        response = requests.post(
            'https://api.zerogpt.com/api/detect/detectText',
            json={'input_text': text},
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            zerogpt_score = round(data.get('data', {}).get('fakePercentage', 0))
            final_score = round((zerogpt_score * 0.7) + (pattern_score * 0.3))
            print(f"  ZeroGPT: {zerogpt_score}% | Pattern: {pattern_score}% | Final: {final_score}%")
            return final_score
        else:
            print(f"  ZeroGPT failed ({response.status_code}), using pattern: {pattern_score}%")
            return pattern_score

    except Exception as e:
        print(f"  ZeroGPT error: {e}, using pattern: {pattern_score}%")
        return pattern_score


# ==========================================
# GEMINI CALL HELPER (new google-genai SDK)
# ==========================================
def call_gemini(prompt: str, temperature: float = 1.4) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            top_k=64,
            max_output_tokens=8192,
        )
    )
    return response.text.strip()


# ==========================================
# HUMANIZER LEVEL 1 - Standard
# ==========================================
def humanize_text_standard(text):
    prompt = f"""You are a master at making AI text completely undetectable by AI detectors like ZeroGPT, GPTZero, Turnitin, and QuillBot.

REWRITE the text below so it sounds 100% like a real human wrote it.

CRITICAL RULES - APPLY EVERY SINGLE ONE:

1. CONTRACTIONS EVERYWHERE: use don't, won't, can't, it's, that's, I'm, you're, we're, they're, isn't, aren't constantly
2. WILD sentence length variation: Mix 3-word fragments with 25+ word sentences randomly. Like this. Short. Then a really long one.
3. Personal fillers: use "honestly", "look", "I mean", "you know", "basically", "frankly", "actually"
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
   - in conclusion → just end naturally
   - it is important to note → delete entirely
   - delve into → look at
   - navigate → handle
   - tapestry, realm, landscape, paradigm → simple word
   - robust → strong
   - seamless → smooth
   - comprehensive → full
   - innovative → new
   - pivotal → key
   - multifaceted → complex
   - it is worth noting → delete
   - this ensures → this means
   - plays a crucial role → matters a lot
8. Add sentence fragments randomly. Like this.
9. Mix formal and casual tone naturally
10. Vary paragraph lengths
11. Use "and" to start sentences sometimes

KEEP ALL FACTS AND MEANING INTACT. Only change HOW it's written.
Return ONLY the rewritten text. No explanations. No quotes.

TEXT TO REWRITE:
{text}"""

    return call_gemini(prompt, temperature=1.4)


# ==========================================
# HUMANIZER LEVEL 2 - Aggressive
# ==========================================
def humanize_text_aggressive(text):
    prompt = f"""The text below still sounds like AI. Make it sound COMPLETELY human.

This needs to FOOL ZeroGPT and GPTZero completely. Score must reach near 0% AI.

DO THIS:
- Restructure sentences completely — don't just swap words
- Add personal opinions: "I've seen this happen a lot", "from what I know"
- Use MORE contractions than feels necessary
- Break grammar rules — start with And, But, So
- Add thinking words: "I mean", "honestly", "look", "basically"
- Make some sentences really short. Like one word. Seriously.
- Then write a long rambling sentence that feels like someone typing their thoughts without stopping to edit
- Use dashes — like this — and (parentheses) for side thoughts
- Remove any remaining formal language completely
- Add a rhetorical question if there isn't one already
- Use "a lot" instead of "many", "get" instead of "obtain", "show" instead of "demonstrate"
- Occasionally repeat an idea in different words like a real human would
- Break into more paragraphs — shorter chunks feel more human

KEEP ALL FACTS. Return ONLY the rewritten text.

TEXT:
{text}"""

    return call_gemini(prompt, temperature=1.6)


# ==========================================
# HUMANIZER LEVEL 3 - Nuclear
# ==========================================
def humanize_text_nuclear(text):
    prompt = f"""This text is STILL being detected as AI-written. COMPLETELY transform it right now.

NUCLEAR HUMANIZATION — maximum effort required:

Rewrite from scratch using the same facts but:
- Write like you're explaining to a close friend in a casual message
- Use very casual but intelligent tone throughout
- Add personal perspective everywhere: "honestly", "in my experience", "I've noticed"
- Make it fully conversational — like someone talking out loud, not writing an essay
- Short punchy sentences mixed with longer flowing ones randomly
- Zero academic structure — absolutely no "firstly, secondly, finally" patterns
- Contractions for EVERY POSSIBLE WORD combination
- Add natural filler phrases: "you know what I mean", "that kind of thing", "stuff like that"
- Break ALL grammar rules naturally — fragments. Conjunctions at start. Run-ons that feel real.
- Use — dashes — and (parentheses) very liberally throughout
- Add 2-3 rhetorical questions naturally placed
- Vary rhythm dramatically — fast punchy then slow flowing
- Replace EVERY formal word with simple everyday words
- Make it feel ALIVE, imperfect, and genuinely human

FACTS MUST STAY 100% THE SAME. Return ONLY the rewritten text. No intro, no explanation.

TEXT:
{text}"""

    return call_gemini(prompt, temperature=1.8)


# ==========================================
# MASTER LOOP - Humanize Until Zero
# ==========================================
def humanize_until_zero(text, target_score=15, max_attempts=6):
    # Step 1: Get original score
    original_score = detect_ai_real(text)
    print(f"📊 Original score: {original_score}%")

    # Step 2: Already below target — return immediately
    if original_score <= target_score:
        print(f"✅ Already below target ({target_score}%). No passes needed.")
        return text, original_score, original_score, 0

    # Step 3: Humanize loop
    best_text = text
    best_score = original_score
    attempt = 0

    while best_score > target_score and attempt < max_attempts:
        attempt += 1
        print(f"🔄 Attempt {attempt}/{max_attempts} — Best so far: {best_score}%")

        try:
            # Escalate level based on attempt
            if attempt <= 2:
                print(f"  → Level 1: Standard (temp 1.4)")
                candidate = humanize_text_standard(best_text)
            elif attempt <= 4:
                print(f"  → Level 2: Aggressive (temp 1.6)")
                candidate = humanize_text_aggressive(best_text)
            else:
                print(f"  → Level 3: Nuclear (temp 1.8)")
                candidate = humanize_text_nuclear(best_text)

            # Score the candidate
            candidate_score = detect_ai_real(candidate)
            print(f"  → Candidate score: {candidate_score}%")

            # Keep only if better
            if candidate_score < best_score:
                best_text = candidate
                best_score = candidate_score
                print(f"  ✓ Improved! New best: {best_score}%")
            else:
                print(f"  ✗ No improvement (best stays: {best_score}%)")

            # Early exit if target reached
            if best_score <= target_score:
                print(f"  🎯 Target reached at attempt {attempt}!")
                break

        except Exception as e:
            print(f"  ✗ Attempt {attempt} error: {e}")
            continue

    print(f"🏁 Final: {best_score}% after {attempt} attempts")
    return best_text, best_score, original_score, attempt


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
# ENDPOINTS
# ==========================================
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


@app.post("/humanize-public")
def humanize_public(data: TextInput):
    if len(data.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 chars)")
    if len(data.text) < 20:
        raise HTTPException(status_code=400, detail="Text too short (min 20 chars)")

    humanized, final_score, original_score, attempts = humanize_until_zero(
        text=data.text,
        target_score=15,
        max_attempts=6
    )

    improvement = original_score - final_score

    return {
        "humanized": humanized,
        "original_ai_score": original_score,
        "final_ai_score": final_score,
        "human_score": 100 - final_score,
        "improvement": improvement,
        "attempts_used": attempts,
        "target_reached": final_score <= 15,
        "already_human": attempts == 0,
        "message": "Already human enough!" if attempts == 0 else f"Humanized in {attempts} passes"
    }


@app.post("/humanize")
def humanize_for_n8n(data: TextInput, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    humanized, final_score, original_score, attempts = humanize_until_zero(
        text=data.text,
        target_score=15,
        max_attempts=6
    )

    improvement = original_score - final_score

    return {
        "content": humanized,
        "text": humanized,
        "humanized": humanized,
        "ai_score": final_score,
        "human_score": 100 - final_score,
        "original_ai_score": original_score,
        "improvement": improvement,
        "attempts_used": attempts,
        "target_reached": final_score <= 15,
        "already_human": attempts == 0,
        "message": "Already human enough!" if attempts == 0 else f"Humanized in {attempts} passes"
    }
