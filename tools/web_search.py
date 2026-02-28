from tavily import TavilyClient
from strands import tool
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # Get the Tavily API key from environment variables

@tool
def web_search(query: str) -> str:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        results = tavily_client.search(query)
        return results
    except Exception as e:
        print(f"Error performing web search: {e}")
        return [f"Error: Unable to perform web search. {str(e)}"]