import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Force load .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    print("Warning: TAVILY_API_KEY not found in .env")
    tavily_client = None
else:
    tavily_client = TavilyClient(api_key=api_key)

def web_search(query: str) -> str:
    """Search the web for current information."""
    if tavily_client is None:
        return "Web search is not available. TAVILY_API_KEY missing."
    try:
        result = tavily_client.search(query, max_results=3)
        return "\n".join([r["content"] for r in result.get("results", [])])
    except Exception as e:
        return f"Search error: {str(e)}"