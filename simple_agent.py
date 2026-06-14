import streamlit as st
import os
import requests
import json
import time
from groq import Groq
from tavily import TavilyClient
from PIL import Image
from io import BytesIO
import tempfile
import base64

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]
aihorde_api_key = st.secrets["AIHORDE_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# ============================================
# IMAGE GENERATION FUNCTION (AI Horde)
# ============================================
def generate_image(prompt):
    """Generate an image using AI Horde via direct API calls"""
    
    try:
        print(f"🎨 Starting image generation for: '{prompt}'")
        
        # AI Horde API base URL
        base_url = "https://aihorde.net/api/v2"
        
        # Step 1: Submit generation request
        submit_payload = {
            "prompt": prompt,
            "params": {
                "width": 512,
                "height": 512,
                "steps": 25,
                "n": 1,
                "sampler_name": "k_euler_a"
            },
            "nsfw": False,
            "censor_nsfw": True,
            "models": ["Deliberate"]
        }
        
        print("📤 Submitting request to AI Horde...")
        
        submit_response = requests.post(
            f"{base_url}/generate/async",
            json=submit_payload,
            headers={"Content-Type": "application/json", "apikey": aihorde_api_key},
            timeout=30
        )
        
        print(f"Response status: {submit_response.status_code}")
        print(f"Response text: {submit_response.text}")
        
        if submit_response.status_code not in [200, 202]:
            print(f"❌ Submission failed: {submit_response.status_code}")
            return None
            
        result = submit_response.json()
        job_id = result.get("id")
        
        if not job_id:
            print("❌ No job ID received")
            return None
            
        print(f"✅ Job submitted. ID: {job_id}")
        
        # Step 2: Poll for completion
        print("⏳ Waiting for generation...")
        max_attempts = 30
        
        for attempt in range(max_attempts):
            time.sleep(2)
            
            check_response = requests.get(
                f"{base_url}/generate/check/{job_id}",
                headers={"apikey": aihorde_api_key},
                timeout=10
            )
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                print(f"Check data: {check_data}")
                if check_data.get("finished") == 1 or check_data.get("done") == 1:
                    print(f"🎉 Generation complete!")
                    break
                    
            print(f"   Attempt {attempt + 1}/{max_attempts} - Processing...")
            
            if attempt >= max_attempts - 1:
                print("❌ Timeout waiting for generation")
                return None
        
        # Step 3: Retrieve the image
        status_response = requests.get(
            f"{base_url}/generate/status/{job_id}",
            headers={"apikey": aihorde_api_key},
            timeout=30
        )
        
        print(f"Status response: {status_response.status_code}")
        
        if status_response.status_code != 200:
            print(f"❌ Status retrieval failed: {status_response.status_code}")
            return None
            
        status_data = status_response.json()
        print(f"Status data keys: {status_data.keys() if status_data else 'None'}")
        
        generations = status_data.get("generations", [])
        print(f"Number of generations: {len(generations)}")
        
        if not generations:
            print("❌ No generations in response")
            return None
            
        generation = generations[0]
        print(f"Generation keys: {generation.keys() if generation else 'None'}")
        
        # Get image data
        img_data = None
        if generation.get("img"):
            print("📥 Found base64 image")
            img_data = base64.b64decode(generation.get("img"))
        elif generation.get("url"):
            print(f"📥 Downloading from URL")
            img_response = requests.get(generation.get("url"), timeout=30)
            if img_response.status_code == 200:
                img_data = img_response.content
        
        if not img_data:
            print("❌ Could not retrieve image data")
            return None
            
        # Save the image
        img = Image.open(BytesIO(img_data))
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        img.save(temp_file.name)
        print(f"✅ Image saved to: {temp_file.name}")
        
        # Clean up
        try:
            requests.delete(f"{base_url}/generate/status/{job_id}", headers={"apikey": aihorde_api_key})
        except:
            pass
            
        return temp_file.name
        
    except Exception as e:
        print(f"🚨 Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================
# WEB SEARCH FUNCTION (Tavily)
# ============================================
def web_search(query, max_results=5):
    """Search the web using Tavily API"""
    try:
        response = tavily.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
            include_answer=True
        )
        
        results = []
        
        if response.get('answer'):
            results.append({
                "title": "AI Summary",
                "body": response['answer'],
                "url": ""
            })
        
        for result in response.get('results', []):
            results.append({
                "title": result.get("title"),
                "body": result.get("content", "No content available."),
                "url": result.get("url")
            })
        
        return results
    except Exception as e:
        return [{"body": f"Search error: {str(e)}"}]

# ============================================
# MAIN AGENT FUNCTION
# ============================================
def run_agent(query):
    """Process user query - handles both image generation and web search"""
    try:
        # Check if it's an image generation request
        image_keywords = ['generate', 'create', 'draw', 'make', 'image of', 'picture of', 'render']
        if any(keyword in query.lower() for keyword in image_keywords):
            # Extract the image prompt
            image_prompt = query
            for keyword in ['generate', 'create', 'draw', 'make', 'an image of', 'a picture of', 'image of', 'picture of', 'render']:
                image_prompt = image_prompt.lower().replace(keyword, '').strip()
            
            if not image_prompt or len(image_prompt) < 3:
                image_prompt = query
            
            print(f"Image prompt: {image_prompt}")
            
            # Generate the image using AI Horde
            image_path = generate_image(image_prompt)
            
            if image_path:
                return f"IMAGE_RESULT:{image_path}|{image_prompt}"
            else:
                return "I couldn't generate that image right now. The AI Horde might be busy. Please try again in a minute."
        
        # If not an image request, perform web search
        search_results = web_search(query)
        
        # Build context from search results
        context_parts = []
        for i, result in enumerate(search_results[:5]):
            if result.get('body'):
                if result.get('title') != "AI Summary":
                    context_parts.append(f"Source {i+1} ({result.get('title', 'Unknown')}): {result['body'][:500]}")
                else:
                    context_parts.append(f"AI Summary: {result['body'][:500]}")
        
        context = "\n\n".join(context_parts) if context_parts else "No relevant information found."
        
        # Create prompt for Groq
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the information below.

SEARCH RESULTS:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Use ONLY the search results above to answer
- If the answer is in the search results, provide it directly
- If the search results don't contain the answer, say "Based on the information I found, I cannot answer this question confidently."
- Be specific and cite your sources when possible

ANSWER:"""

        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)}"