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

# ============================================
# IMPORTANT: Set Fal.ai API key as environment variable
# ============================================
# The Fal client reads from FAL_KEY environment variable automatically[citation:1]
# So we set it BEFORE importing fal_client
os.environ["FAL_KEY"] = st.secrets["FAL_API_KEY"]

# Now import fal_client (it will read FAL_KEY from environment)
import fal_client

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# ============================================
# IMAGE GENERATION FUNCTION (Fal.ai)
# ============================================
def generate_image(prompt, max_retries=3):
    """Generate an image using Fal.ai's Flux Schnell model"""
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}: Generating image for: {prompt}")
            
            # Using the exact syntax from Fal.ai documentation[citation:6][citation:10]
            result = fal_client.subscribe(
                "fal-ai/flux/schnell",
                arguments={
                    "prompt": prompt,
                    "image_size": "square_hd"
                }
            )
            
            print(f"Result received: {result is not None}")
            
            # Extract the image URL from the result
            if result and 'images' in result and len(result['images']) > 0:
                image_url = result['images'][0]['url']
                print(f"Downloading from: {image_url[:50]}...")
                
                # Download the image
                response = requests.get(image_url, timeout=30)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    img.save(temp_file.name)
                    print(f"SUCCESS: Image saved to {temp_file.name}")
                    return temp_file.name
                else:
                    print(f"Download failed: Status {response.status_code}")
            else:
                print(f"No image in response: {result.keys() if result else 'None'}")
                
        except Exception as e:
            print(f"Attempt {attempt + 1} FAILED: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
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
            
            print(f"Image prompt extracted: {image_prompt}")
            
            # Generate the image
            image_path = generate_image(image_prompt)
            
            if image_path:
                return f"IMAGE_RESULT:{image_path}|{image_prompt}"
            else:
                return "I couldn't generate that image right now. Please check the logs for details."
        
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