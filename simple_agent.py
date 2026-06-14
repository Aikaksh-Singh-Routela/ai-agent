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
import fal_client

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]
fal_api_key = st.secrets["FAL_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# Set Fal.ai API key
fal_client.api_key = fal_api_key

# ============================================
# IMAGE GENERATION FUNCTION (Fal.ai - Free & Fast)
# ============================================
def generate_image(prompt, width=1024, height=768):
    """Generate an image using Fal.ai's Flux model (completely free)"""
    try:
        result = fal_client.subscribe(
            "fal-ai/flux-schnell",
            arguments={
                "prompt": prompt,
                "image_size": f"{width}x{height}"
            }
        )
        
        # Get the image URL from the result
        image_url = result['images'][0]['url']
        
        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name)
            return temp_file.name
        
        return None
    except Exception as e:
        print(f"Fal.ai image generation error: {e}")
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
        
        # Include Tavily's AI-generated answer if available
        if response.get('answer'):
            results.append({
                "title": "AI Summary",
                "body": response['answer'],
                "url": ""
            })
        
        # Include individual search results
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
        image_keywords = ['generate', 'create', 'draw', 'make', 'image of', 'picture of', 'render', 'an image of']
        if any(keyword in query.lower() for keyword in image_keywords):
            # Extract the image prompt (remove the action words)
            image_prompt = query
            for keyword in ['generate', 'create', 'draw', 'make', 'an image of', 'a picture of', 'image of', 'picture of', 'render']:
                image_prompt = image_prompt.lower().replace(keyword, '').strip()
            
            # If nothing left, use the original query
            if not image_prompt or len(image_prompt) < 3:
                image_prompt = query
            
            # Generate the image using Fal.ai
            image_path = generate_image(image_prompt)
            
            if image_path:
                return f"IMAGE_RESULT:{image_path}|{image_prompt}"
            else:
                return "I couldn't generate that image right now. Please try a different description."
        
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