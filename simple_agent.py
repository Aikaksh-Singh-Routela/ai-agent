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
import replicate

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]
replicate_api_token = st.secrets["REPLICATE_API_TOKEN"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# ============================================
# IMAGE GENERATION FUNCTION (Replicate FLUX)
# ============================================
def generate_image(prompt, width=1024, height=768):
    """Generate an image using Replicate's FLUX Schnell model"""
    try:
        # Using FLUX Schnell - fast and cheap (~$0.003 per image)
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_outputs": 1,
                "output_format": "png"
            }
        )
        
        # output is a list of URLs
        if output and len(output) > 0:
            # Download the image from the URL
            response = requests.get(output[0])
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                img.save(temp_file.name)
                return temp_file.name
        
        return None
        
    except Exception as e:
        print(f"Replicate image generation error: {e}")
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
            
            # Generate the image using Replicate
            image_path = generate_image(image_prompt)
            
            if image_path:
                return f"IMAGE_RESULT:{image_path}|{image_prompt}"
            else:
                return "I couldn't generate that image right now. Please try a different description or check your Replicate credits."
        
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