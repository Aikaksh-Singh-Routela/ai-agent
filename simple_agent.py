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

# Your existing agent code below...
# (keep the rest of your functions that use web_search)
