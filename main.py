from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MY_SECRET_KEY = os.getenv("MY_API_KEY")

class TextInput(BaseModel):
    text: str

@app.get("/")
def home():
    return {"message": "Humanizer API v3.0 is running 🚀"}

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

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
    prompt = f"""Restructure this text to break AI patterns. Mix sentence lengths drastically. Replace AI words: utilize→use, facilitate→help, leverage→use, moreover/furthermore→and, however→but. Delete "in conclusion" and "it is important to note". Keep all facts. Return ONLY the rewritten text.

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

@app.post("/humanize")
def humanize(data: TextInput, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    stage1 = pass_1_restructure(data.text)
    stage2 = pass_2_human_voice(stage1)
    stage3 = pass_3_imperfections(stage2)
 return {
    "content": stage3,
    "text": stage3,
    "original": data.text,
    "humanized": stage3
}
