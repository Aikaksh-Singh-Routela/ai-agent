import streamlit as st
import os
import requests
import json
import time
import re
from groq import Groq
from tavily import TavilyClient

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize Tavily client
tavily = TavilyClient(api_key=tavily_api_key)

# ============================================
# MATH PROBLEM SOLVING FUNCTION
# ============================================
def solve_math(expression):
    """Safely solve math problems"""
    try:
        # Clean the expression
        cleaned = expression.lower()
        
        # Common math phrases to handle
        cleaned = cleaned.replace('what is', '')
        cleaned = cleaned.replace('calculate', '')
        cleaned = cleaned.replace('solve', '')
        cleaned = cleaned.replace('plus', '+')
        cleaned = cleaned.replace('minus', '-')
        cleaned = cleaned.replace('times', '*')
        cleaned = cleaned.replace('multiplied by', '*')
        cleaned = cleaned.replace('divided by', '/')
        cleaned = cleaned.replace('percent of', '* 0.01 *')
        
        # Handle square root
        if 'square root of' in cleaned:
            import math
            number = re.search(r'square root of (\d+)', cleaned)
            if number:
                result = math.sqrt(float(number.group(1)))
                return f"🧮 √{number.group(1)} = {result}"
        
        # Handle percentage calculations
        if '%' in cleaned or 'percent' in cleaned:
            # Example: "15% of 200"
            percent_pattern = r'(\d+(?:\.\d+)?)\s*%?\s*(?:of|percent of)?\s*(\d+(?:\.\d+)?)'
            match = re.search(percent_pattern, cleaned)
            if match:
                percent = float(match.group(1))
                number = float(match.group(2))
                result = (percent / 100) * number
                return f"🧮 {percent}% of {number} = {result}"
        
        # Extract numbers and operators for basic math
        pattern = r'[0-9\.\+\-\*\/\(\)\s]+'
        match = re.search(pattern, cleaned)
        
        if match:
            math_expr = match.group().strip()
            # Safely evaluate the expression
            result = eval(math_expr)
            # Format result nicely
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 4)
            return f"🧮 {math_expr} = {result}"
        else:
            return None
            
    except Exception as e:
        print(f"Math error: {e}")
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
    """Process user query - handles math problems and web search"""
    try:
        print(f"Processing query: {query}")
        
        # Check if it's a math problem first
        math_indicators = ['calculate', 'solve', 'what is', 'plus', 'minus', 'times', 
                          'divided by', '%', 'percent', 'square root', '+', '-', '*', '/']
        
        if any(indicator in query.lower() for indicator in math_indicators):
            # Try to solve as math
            math_result = solve_math(query)
            if math_result:
                return math_result
        
        # If not math or math failed, perform web search
        print("Performing web search...")
        search_results = web_search(query)
        
        # Build context from search results
        context_parts = []
        for i, result in enumerate(search_results[:5]):
            if result.get('body'):
                if result.get('title') != "AI Summary":
                    context_parts.append(f"Source {i+1} ({result.get('title', 'Unknown')}): {result['body'][:800]}")
                else:
                    context_parts.append(f"AI Summary: {result['body'][:800]}")
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant information found."
        
        # Create prompt for Groq
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the information below.

SEARCH RESULTS:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Use ONLY the search results above to answer
- If the answer is in the search results, provide it directly with citations
- If the search results don't contain the answer, say "Based on the information I found, I cannot answer this question confidently."
- Be specific, factual, and cite which source you're using
- Keep your answer concise but informative

ANSWER:"""

        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)}"