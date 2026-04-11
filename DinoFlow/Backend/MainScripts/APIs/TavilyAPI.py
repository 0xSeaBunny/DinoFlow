"""TavilyAPI - Advanced web search with AI-optimized results."""
import requests
import os
import sys
from typing import List, Dict, Optional, Any


class TavilyAPI:

    BASE_URL = "https://api.tavily.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        time_range: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        max_results: int = 10,
        include_answer: bool = False,
        include_raw_content: bool = False
    ) -> Dict[str, Any]:

        max_results = max(1, min(max_results, 20))

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content
        }

        if time_range:
            payload["time_range"] = time_range

        if include_domains:
            payload["include_domains"] = include_domains

        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        try:
            response = requests.post(
                f"{self.BASE_URL}/search",
                json=payload,
                timeout=60 if search_depth == "comprehensive" else 30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Tavily API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def extract(self, urls: List[str]) -> Dict[str, Any]:

        urls = urls[:20]

        payload = {
            "api_key": self.api_key,
            "urls": urls
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/extract",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Tavily extract request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


def load_tavily_credentials(script_dir: Optional[str] = None) -> Optional[str]:

    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))

    tavily_path = os.path.join(script_dir, "Backend", "SavedInfo", "Tavily.txt")

    if not os.path.isfile(tavily_path):
        return None

    try:
        with open(tavily_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("api_key:"):
                    return line.split(":", 1)[1].strip()
    except Exception as e:
        print(f"Error loading Tavily credentials: {e}")

    return None


def create_tavily_api(script_dir: Optional[str] = None) -> Optional[TavilyAPI]:
    api_key = load_tavily_credentials(script_dir)

    if not api_key:
        return None

    return TavilyAPI(api_key)
