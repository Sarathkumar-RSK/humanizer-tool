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
            print(f"  ZeroGPT failed ({response.status_code}), using pattern score: {pattern_score}%")
            return pattern_score

    except Exception as e:
        print(f"  ZeroGPT error: {e}, using pattern score: {pattern_score}%")
        return pattern_score


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
- Then write a long rambling sentence that feels like someone typing their thoughts
- Use dashes — like this — and (parentheses) for side thoughts
- Remove any remaining formal language
- Add a rhetorical question if there isn't one
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
# HUMANIZER LEVEL 3 - Nuclear
# ==========================================
def humanize_text_nuclear(text):
    prompt = f"""This text is still being detected as AI-written. COMPLETELY transform it.

NUCLEAR HUMANIZATION — maximum effort:

Rewrite from scratch using the same facts but:
- Write like you're explaining to a friend in a casual message
- Use very casual but intelligent tone
- Add personal perspective: "honestly", "in my experience", "I've noticed"
- Make it conversational — like someone talking, not writing an essay
- Short punchy sentences mixed with longer flowing ones
- No academic structure — no "firstly, secondly, finally"
- Contractions for EVERY POSSIBLE WORD
- Add filler phrases: "you know what I mean", "that kind of thing"
- Break rules — fragments. Conjunctions at start. Run-ons that feel natural.
- Use — dashes — and (parentheses) liberally
- Add 2-3 rhetorical questions
- Vary rhythm dramatically
- Replace ALL formal words with simple everyday words
- Make it feel ALIVE and slightly imperfect

FACTS MUST STAY THE SAME. Return ONLY the rewritten text.

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
# MASTER LOOP - Humanize Until Zero
# ==========================================
def humanize_until_zero(text, target_score=15, max_attempts=6):
    # Step 1: Get original score
    original_score = detect_ai_real(text)
    print(f"📊 Original score: {original_score}%")

    # Step 2: Already below target — no work needed
    if original_score <= target_score:
        print(f"✅ Already below target ({target_score}%). Returning original.")
        return text, original_score, original_score, 0

    # Step 3: Start humanizing loop
    best_text = text
    best_score = original_score
    attempt = 0

    while best_score > target_score and attempt < max_attempts:
        attempt += 1
        print(f"🔄 Attempt {attempt}/{max_attempts} — Best so far: {best_score}%")

        try:
            # Pick level based on attempt number
            if attempt <= 2:
                print(f"  → Level 1: Standard")
                candidate = humanize_text_standard(best_text)
            elif attempt <= 4:
                print(f"  → Level 2: Aggressive")
                candidate = humanize_text_aggressive(best_text)
            else:
                print(f"  → Level 3: Nuclear")
                candidate = humanize_text_nuclear(best_text)

            # Score the new version
            candidate_score = detect_ai_real(candidate)
            print(f"  → Result: {candidate_score}%")

            # Keep it only if it's better
            if candidate_score < best_score:
                best_text = candidate
                best_score = candidate_score
                print(f"  ✓ Improved to {best_score}%")
            else:
                print(f"  ✗ No improvement, keeping best ({best_score}%)")

            # Stop early if target reached
            if best_score <= target_score:
                print(f"  🎯 Target reached at attempt {attempt}!")
                break

        except Exception as e:
            print(f"  ✗ Attempt {attempt} error: {e}")
            continue

    print(f"🏁 Done — Final: {best_score}% | Attempts: {attempt}")
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
