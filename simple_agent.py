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
from horde_sdk import APIToken, AIHordeAPI
from horde_sdk.generations import ImageGenerationInput, ImageGenerationParams

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# Initialize AI Horde API (no API key needed - anonymous access)
horde_api = AIHordeAPI(APIToken("0000000000"))  # Dummy key works for anonymous access

# ============================================
# IMAGE GENERATION FUNCTION (AI Horde - Free)
# ============================================
def generate_image(prompt, max_retries=30):
    """Generate an image using AI Horde (completely free, no API key needed)"""
    
    try:
        print(f"Generating image for: {prompt}")
        
        # Create the generation request
        gen_input = ImageGenerationInput(
            prompt=prompt,
            params=ImageGenerationParams(
                width=512,
                height=512,
                steps=25,
                n=1
            ),
            nsfw=False,
            censor_nsfw=True,
            models=["Anything Diffusion"]
        )
        
        # Submit the request
        print("Submitting request to AI Horde...")
        response = horde_api.image_generation_request(gen_input)
        generation_id = response.id
        print(f"Request submitted. Generation ID: {generation_id}")
        
        # Poll for completion
        for attempt in range(max_retries):
            time.sleep(2)  # Wait 2 seconds between checks
            print(f"Checking status... (attempt {attempt + 1}/{max_retries})")
            
            status = horde_api.image_generation_status(generation_id)
            
            if status.done == 1:
                print("Generation complete!")
                generations = status.generations
                
                if generations and len(generations) > 0:
                    # Decode the base64 image
                    image_data = base64.b64decode(generations[0].img)
                    img = Image.open(BytesIO(image_data))
                    
                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    img.save(temp_file.name)
                    print(f"Image saved to: {temp_file.name}")
                    return temp_file.name
                else:
                    print("No generations returned")
                    return None
                    
            elif attempt >= max_retries - 1:
                print("Timeout waiting for generation")
                return None
        
        return None
        
    except Exception as e:
        print(f"AI Horde generation error: {e}")
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