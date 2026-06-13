import streamlit as st
import os
import requests
import json
import time
from groq import Groq
from tavily import TavilyClient

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# Tavily search function
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

# Main agent function
def run_agent(query):
    """Process user query and return response using Groq LLM with Tavily search"""
    try:
        # Check if it's an image generation request
        image_keywords = ['generate', 'create', 'draw', 'make', 'image of', 'picture of']
        if any(keyword in query.lower() for keyword in image_keywords):
            return "Image generation feature coming soon! For now, try asking a factual question."
        
        # Perform web search using Tavily
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
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)}"
