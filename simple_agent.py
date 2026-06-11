import streamlit as st

# At the start of your app, add:
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]

from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json
import time
import streamlit as st
from groq import Groq

# Initialize Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Available tools
def web_search(query: str) -> str:
    """Search the web"""
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        result = tavily.search(query, max_results=2)
        return "\n".join([r["content"] for r in result.get("results", [])])
    except Exception as e:
        return f"Search error: {str(e)}"

def calculate(expression: str) -> str:
    """Calculate math"""
    try:
        allowed = set("0123456789+-*/.()% ")
        clean = "".join(c for c in expression if c in allowed)
        return str(eval(clean))
    except:
        return "Calculation error"

def generate_image(prompt: str) -> str:
    """Generate image using AI Horde"""
    try:
        print(f"🎨 Generating image for: {prompt}")
        
        submit = requests.post(
            "https://aihorde.net/api/v2/generate/async",
            headers={"apikey": "NoZGwZL4_VLH-d6t1nOQBA", "Content-Type": "application/json"},
            json={"prompt": prompt, "params": {"width": 512, "height": 512, "steps": 25}},
            timeout=60
        )
        
        if submit.status_code != 202:
            return f"Image generation failed: Status {submit.status_code}"
        
        job_id = submit.json()["id"]
        print(f"🆔 Job ID: {job_id}")
        print(f"⏳ Waiting for image to generate...")
        
        # Wait up to 3 minutes (36 checks x 5 seconds = 180 seconds)
        for attempt in range(120):  # 120 x 5 seconds = 10 minutes
            time.sleep(5)
            status = requests.get(f"https://aihorde.net/api/v2/generate/status/{job_id}", timeout=30)
            data = status.json()
            
            if data.get("done"):
                img_url = data["generations"][0]["img"]
                print(f"✅ Image generated!")
                return img_url
            
            waiting = data.get("waiting", 0)
            processing = data.get("processing", 0)
            print(f"⏳ Attempt {attempt+1}/120 - Waiting: {waiting}, Processing: {processing}")
        
        return "Timeout - AI Horde is very busy. Please try again in a few minutes."
    except Exception as e:
        return f"Image error: {str(e)}"

def run_simple_agent(user_input: str) -> str:
    """Simple agent that decides which tool to use"""
    
    input_lower = user_input.lower()
    
    # Calculator
    if any(word in input_lower for word in ["calculate", "multiply", "divide", "add", "subtract", "math", "*", "+", "-", "/"]):
        import re
        numbers = re.findall(r'\d+', user_input)
        if len(numbers) >= 2:
            if "multiply" in input_lower or "*" in input_lower:
                result = int(numbers[0]) * int(numbers[1])
                return f"The result of {numbers[0]} × {numbers[1]} = {result}"
            elif "divide" in input_lower or "/" in input_lower:
                result = int(numbers[0]) / int(numbers[1])
                return f"The result of {numbers[0]} ÷ {numbers[1]} = {result}"
            elif "add" in input_lower or "+" in input_lower:
                result = int(numbers[0]) + int(numbers[1])
                return f"The result of {numbers[0]} + {numbers[1]} = {result}"
            elif "subtract" in input_lower or "-" in input_lower:
                result = int(numbers[0]) - int(numbers[1])
                return f"The result of {numbers[0]} - {numbers[1]} = {result}"
    
    # Image generation
    if any(word in input_lower for word in ["generate", "create", "make", "draw", "image", "picture", "photo"]):
        # Extract the prompt (remove command words)
        prompt = user_input
        for word in ["generate", "create", "make", "draw", "an", "a", "image", "of", "picture", "photo"]:
            prompt = prompt.replace(word, "")
        prompt = prompt.strip()
        if not prompt:
            prompt = "a beautiful landscape"
        return generate_image(prompt)
    
    # Web search (default for questions)
    if any(word in input_lower for word in ["what", "who", "where", "when", "why", "how", "tell me", "search"]):
        try:
            result = web_search(user_input)
            if result and "error" not in result.lower():
                return result
        except:
            pass
    
    # Fallback to Groq API for general questions
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_input}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I couldn't process your request: {str(e)}"

def run_agent(user_input: str) -> str:
    return run_simple_agent(user_input)