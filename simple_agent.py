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

# Correct imports from horde-sdk documentation
from horde_sdk import AIHordeAPISimpleClient
from horde_sdk.generations import ImageGenerationInput, ImageGenerationParams

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# Initialize AI Horde client (no API key needed - uses anonymous access)
horde_client = AIHordeAPISimpleClient()

# ============================================
# IMAGE GENERATION FUNCTION (AI Horde - Free)
# ============================================
def generate_image(prompt, max_retries=30):
    """Generate an image using AI Horde (completely free, no API key needed)"""
    
    try:
        print(f"Generating image for: {prompt}")
        
        # Create the generation request using the correct SDK types
        generation_input = ImageGenerationInput(
            prompt=prompt,
            params=ImageGenerationParams(
                width=512,
                height=512,
                steps=25,
                n=1
            ),
            nsfw=False,
            censor_nsfw=True
        )
        
        # Submit the request using the simple client (handles polling automatically)
        print("Submitting request to AI Horde...")
        
        # The simple client's generate method handles the entire process
        # It submits and waits for completion automatically
        generations = horde_client.generate(generation_input)
        
        if generations and len(generations) > 0:
            # The image comes as base64 string
            image_data = generations[0].img  # This is already bytes or base64
            import base64
            
            # If it's a string, it's base64; if it's bytes, use directly
            if isinstance(image_data, str):
                img_bytes = base64.b64decode(image_data)
            else:
                img_bytes = image_data
                
            img = Image.open(BytesIO(img_bytes))
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name)
            print(f"Image saved to: {temp_file.name}")
            return temp_file.name
        else:
            print("No generations returned")
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