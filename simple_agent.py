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

# --- CORRECTED IMPORTS FOR HORDE-SDK ---
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest
# ---------------------------------------

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# ============================================
# IMAGE GENERATION FUNCTION (AI Horde)
# ============================================
def generate_image(prompt):
    """Generate an image using AI Horde (completely free, no API key needed)"""
    try:
        print(f"🎨 Starting image generation for: '{prompt}'")
        
        # Initialize the client inside the function
        horde_client = AIHordeAPISimpleClient()
        
        # Create the request object
        generation_request = ImageGenerateAsyncRequest(
            prompt=prompt,
            nsfw=False,
            censor_nsfw=True,
            r2=True,  # Use R2 for a stable download link
            params={
                "width": 512,
                "height": 512,
                "steps": 25,
                "n": 1
            }
        )
        
        # Submit the job
        print("📤 Submitting request to AI Horde...")
        initial_response = horde_client.submit_request(generation_request)
        
        # Get the job ID
        job_id = initial_response.id_
        print(f"✅ Job submitted successfully. Job ID: {job_id}")
        
        # Poll for completion
        from horde_sdk.ai_horde_api.apimodels import ImageGenerateCheckRequest
        
        print("⏳ Waiting for the AI Horde to process your request...")
        max_attempts = 45
        for attempt in range(max_attempts):
            time.sleep(2)
            
            check_request = ImageGenerateCheckRequest(job_id=job_id)
            check_response = horde_client.submit_request(check_request)
            
            if check_response.is_finished:
                print(f"🎉 Job finished! Duration: {check_response.processing_time} seconds")
                break
            elif attempt >= max_attempts - 1:
                print("❌ Timeout: The request took too long.")
                return None
        
        # Retrieve the generated image
        from horde_sdk.ai_horde_api.apimodels import ImageGenerateStatusRequest
        
        status_request = ImageGenerateStatusRequest(job_id=job_id)
        final_response = horde_client.submit_request(status_request)
        
        if final_response.generations and len(final_response.generations) > 0:
            # Get the image data
            if final_response.generations[0].img:
                print("📥 Processing image from Base64 data...")
                image_data = base64.b64decode(final_response.generations[0].img)
            elif final_response.generations[0].url:
                print(f"📥 Downloading image from URL...")
                img_response = requests.get(final_response.generations[0].url)
                img_response.raise_for_status()
                image_data = img_response.content
            else:
                print("❌ No image data found in the response.")
                return None

            # Save the image
            img = Image.open(BytesIO(image_data))
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name)
            print(f"✅ Image successfully generated and saved!")
            return temp_file.name
        else:
            print("❌ No generations found in the final response.")
            return None

    except Exception as e:
        print(f"🚨 An unexpected error occurred: {e}")
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