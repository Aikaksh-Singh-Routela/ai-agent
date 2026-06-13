import streamlit as st
import os
import requests
import json
import time
from groq import Groq
from duckduckgo_search import DDGS

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# DuckDuckGo search function (replaces Tavily)
def web_search(query, max_results=5):
    """Search the web using DuckDuckGo (no API key needed)"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        return [{"body": f"Search error: {str(e)}"}]

# Main agent function that app.py imports
def run_agent(query):
    """Process user query and return response using Groq LLM"""
    try:
        # Perform web search to get context
        search_results = web_search(query)
        
        # Extract relevant information from search results
        context = ""
        if search_results and len(search_results) > 0:
            for result in search_results[:3]:  # Use top 3 results
                if 'body' in result:
                    context += result['body'] + "\n\n"
        
        # If no search results, use just the query
        if not context:
            context = f"User asked: {query}"
        
        # Create prompt for Groq
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the following context from web search.

Context:
{context}

User Question: {query}

Instructions:
1. Answer based on the context provided
2. If the answer isn't in the context, say so
3. Be concise and helpful

Answer:"""

        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)}"
