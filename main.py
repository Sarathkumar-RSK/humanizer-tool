from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MY_SECRET_KEY = os.getenv("MY_API_KEY")

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


class TextInput(BaseModel):
    text: str


# ========================================
# WEBSITE - Show HTML page at root
# ========================================
@app.get("/")
def home():
    return FileResponse("static/index.html")


# ========================================
# API Status check
# ========================================
@app.get("/status")
def status():
    return {"message": "Humanizer API v4.0 is running", "status": "online"}


# ========================================
# SECURITY CHECK (for n8n)
# ========================================
def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ========================================
# CALL GROQ AI
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
# HUMANIZER STAGES
# ========================================
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


# ========================================
# SECURE ENDPOINT (for n8n - requires API key)
# ========================================
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


# ========================================
# PUBLIC ENDPOINT (for website - no key needed)
# ========================================
@app.post("/humanize-public")
def humanize_public(data: TextInput):
    # Rate limit: only short texts allowed for public use
    if len(data.text) > 5000:
        raise HTTPException(
            status_code=400, 
            detail="Text too long. Maximum 5000 characters for public use."
        )
    
    result = humanize_text(data.text)
    return {
        "content": result,
        "humanized": result
    }
