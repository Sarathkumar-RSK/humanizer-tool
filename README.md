# humanizer-tool
# humanizer-tool
[main.py](https://github.com/user-attachments/files/28879117/main.py)

from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os

# Load secret key
load_dotenv()

# Create API
app = FastAPI()

# Connect to Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Input format
class TextInput(BaseModel):
    text: str

# Home
@app.get("/")
def home():
    return {"message": "Humanizer API v3.0 (Multi-Stage) is running 🚀"}


# ========================================
# HELPER FUNCTION: Call Groq AI
# ========================================
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


# ========================================
# PASS 1: Break AI Patterns (Restructure)
# ========================================
def pass_1_restructure(text):
    system = "You are an expert editor who breaks robotic AI writing patterns by restructuring text."
    
    prompt = f"""Restructure the text below to break AI patterns. Focus ONLY on structure, not voice yet.

RULES:
1. Break up long sentences into shorter ones (or merge short ones into longer)
2. Mix sentence lengths drastically (3-word sentences with 30-word ones)
3. Change passive voice to active voice
4. Reorder ideas within paragraphs
5. Replace these AI words:
   - "utilize" → "use"
   - "facilitate" → "help"  
   - "implement" → "do" or "set up"
   - "leverage" → "use"
   - "moreover/furthermore/additionally" → "and" or "also" or "plus"
   - "however" → "but"
   - "in conclusion" → DELETE entirely
   - "it is important to note" → DELETE entirely
6. Keep ALL facts and meaning the same
7. Return ONLY the restructured text, no intro or explanation

TEXT:
{text}
"""
    return call_groq(system, prompt, temp=0.9)


# ========================================
# PASS 2: Add Human Voice
# ========================================
def pass_2_human_voice(text):
    system = "You are a tired blogger from a small town. You write casually, like you're talking to a friend over coffee. You hate corporate-speak."
    
    prompt = f"""Rewrite this text in YOUR voice - casual, opinionated, conversational. Add human personality.

RULES:
1. Use contractions everywhere: don't, can't, won't, it's, you're, I've, that's
2. Add filler words naturally: "honestly", "look", "basically", "kind of", "you know", "I mean"
3. Inject mild opinions: "honestly, this is overhyped", "in my experience", "from what I've seen"
4. Use rhetorical questions: "But does it really work?", "Sounds great, right?"
5. Add casual transitions: start sentences with "And", "But", "So", "Now"
6. Use em-dashes for emphasis: "It works — most of the time"
7. Add parenthetical asides: "(and trust me on this)", "(yeah, really)"
8. Show slight skepticism: "supposedly", "apparently", "allegedly"
9. Keep all facts and information
10. Return ONLY the rewritten text

TEXT:
{text}
"""
    return call_groq(system, prompt, temp=1.0)


# ========================================
# PASS 3: Final Human Imperfections
# ========================================
def pass_3_imperfections(text):
    system = "You are a real human writer who adds natural imperfections to make text undetectable by AI detectors."
    
    prompt = f"""Polish this text with natural human imperfections. Final pass to make it 100% human.

RULES:
1. Add sentence fragments occasionally: "Not great. Not terrible either."
2. Use slightly redundant phrases sometimes (humans repeat themselves)
3. Vary paragraph lengths drastically (one paragraph could be 1 sentence, next could be 5)
4. Start some sentences with conjunctions: "And", "But", "So", "Because"
5. Add subtle hedging: "kind of", "sort of", "more or less", "I guess"
6. Use everyday vocabulary, avoid fancy synonyms
7. Make sure NO sentences sound like AI:
   - Avoid "delve into", "navigate through", "embark on"
   - Avoid "tapestry", "realm", "landscape", "journey"
   - Avoid "robust", "seamless", "comprehensive", "innovative"
   - Avoid "in today's fast-paced world"
8. Don't make it perfect - add small natural quirks
9. Keep all facts
10. Return ONLY the polished text, nothing else

TEXT:
{text}
"""
    return call_groq(system, prompt, temp=1.1)


# ========================================
# MAIN HUMANIZER ENDPOINT (Multi-Stage)
# ========================================
@app.post("/humanize")
def humanize(data: TextInput):
    
    original = data.text
    
    # Stage 1: Restructure
    print("Stage 1: Restructuring...")
    stage1 = pass_1_restructure(original)
    
    # Stage 2: Add human voice
    print("Stage 2: Adding human voice...")
    stage2 = pass_2_human_voice(stage1)
    
    # Stage 3: Final polish
    print("Stage 3: Adding imperfections...")
    stage3 = pass_3_imperfections(stage2)
    
    return {
        "original": original,
        "humanized": stage3,
        "stages": {
            "stage1_restructured": stage1,
            "stage2_human_voice": stage2,
            "stage3_final": stage3
        }
    }
    
