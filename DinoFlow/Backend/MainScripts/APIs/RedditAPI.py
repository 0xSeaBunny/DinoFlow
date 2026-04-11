import requests
import base64
import time
import os
import sys
from typing import List, Dict, Optional, Any


class RedditAuth:
    
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    USER_AGENT = "DinoFlow/1.0 (by /u/DinoFlowUser)"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.expires_at: float = 0
    
    def _get_basic_auth(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def get_access_token(self) -> Optional[str]:
        if self.access_token and time.time() < self.expires_at - 60:
            return self.access_token
        
        try:
            headers = {
                "Authorization": self._get_basic_auth(),
                "User-Agent": self.USER_AGENT
            }
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(
                self.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            self.expires_at = time.time() + expires_in
            
            return self.access_token
        except Exception as e:
            print(f"Reddit auth error: {e}")
            return None
    
    def get_headers(self) -> Dict[str, str]:
        token = self.get_access_token()
        if not token:
            raise RuntimeError("Failed to get Reddit access token")
        
        return {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.USER_AGENT
        }


class RedditAPI:
    
    BASE_URL = "https://oauth.reddit.com"
    
    def __init__(self, auth: RedditAuth):
        self.auth = auth
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            headers = self.auth.get_headers()
            url = f"{self.BASE_URL}{endpoint}"
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Reddit API request error: {e}")
            return None
    
    def _extract_post_data(self, post: Dict) -> Dict[str, Any]:
        data = post.get("data", {})
        return {
            "title": data.get("title", ""),
            "url": data.get("url", ""),
            "permalink": data.get("permalink", ""),
            "selftext": data.get("selftext", ""),
            "id": data.get("id", "")
        }
    
    def _extract_comments(self, comments_list: List[Dict], max_depth: int = 3, current_depth: int = 0) -> List[Dict]:
        if current_depth >= max_depth:
            return []
        
        result = []
        for comment in comments_list:
            if not isinstance(comment, dict):
                continue
            
            data = comment.get("data", {})
            body = data.get("body", "")
            
            if body in ("[deleted]", "[removed]", ""):
                continue
            
            comment_data = {"body": body}
            
            replies = data.get("replies", "")
            if isinstance(replies, dict) and current_depth < max_depth - 1:
                reply_data = replies.get("data", {})
                children = reply_data.get("children", [])
                child_comments = self._extract_comments(children, max_depth, current_depth + 1)
                if child_comments:
                    comment_data["replies"] = child_comments
            
            result.append(comment_data)
        
        return result
    
    def search_posts(
        self,
        query: str,
        subreddit: Optional[str] = None,
        sort: str = "relevance",
        limit: int = 10,
        top_comments: int = 5
    ) -> List[Dict[str, Any]]:

        limit = min(limit, 25)
        
        params = {
            "q": query,
            "sort": sort,
            "limit": limit,
            "type": "posts"
        }
        
        if subreddit:
            params["restrict_sr"] = "true"
            endpoint = f"/r/{subreddit}/search"
        else:
            endpoint = "/search"
        
        data = self._make_request(endpoint, params)
        if not data:
            return []
        
        results = []
        posts = data.get("data", {}).get("children", [])
        
        for post in posts:
            post_data = self._extract_post_data(post)
            post_id = post_data.get("id")
            
            if post_id:
                comments = self.get_post_comments(post_id, depth=1, limit=top_comments)
                post_data["top_comments"] = [c.get("body", "") for c in comments]
            
            results.append(post_data)
        
        return results
    
    def get_post_comments(
        self,
        post_id: str,
        depth: int = 3,
        limit: int = 100
    ) -> List[Dict]:

        params = {
            "depth": depth,
            "limit": limit,
            "sort": "top"
        }
        
        endpoint = f"/comments/{post_id}"
        data = self._make_request(endpoint, params)
        
        if not data or len(data) < 2:
            return []
        
        comments_data = data[1].get("data", {}).get("children", [])
        return self._extract_comments(comments_data, max_depth=depth)
    
    def get_full_thread(
        self,
        permalink: str,
        max_depth: int = 10,
        max_comments: int = 200
    ) -> Optional[Dict[str, Any]]:

        parts = permalink.strip("/").split("/")
        if len(parts) < 4 or parts[0] != "r":
            return None
        
        post_id = parts[3]
        
        params = {
            "depth": max_depth,
            "limit": max_comments,
            "sort": "top"
        }
        
        endpoint = f"/comments/{post_id}"
        data = self._make_request(endpoint, params)
        
        if not data or len(data) < 2:
            return None
        
        post_data = self._extract_post_data(data[0].get("data", {}).get("children", [{}])[0])
        
        comments_data = data[1].get("data", {}).get("children", [])
        comments = self._extract_comments(comments_data, max_depth=max_depth)
        
        return {
            "title": post_data.get("title", ""),
            "selftext": post_data.get("selftext", ""),
            "url": post_data.get("url", ""),
            "permalink": post_data.get("permalink", ""),
            "comments": comments
        }


def load_reddit_credentials(script_dir: Optional[str] = None) -> tuple:

    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))

    reddit_path = os.path.join(script_dir, "Backend", "SavedInfo", "RedditInfo.txt")
    
    if not os.path.isfile(reddit_path):
        return None, None
    
    client_id = None
    client_secret = None
    
    try:
        with open(reddit_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("client_id:"):
                    client_id = line.split(":", 1)[1].strip()
                elif line.startswith("client_secret:"):
                    client_secret = line.split(":", 1)[1].strip()
    except Exception as e:
        print(f"Error loading Reddit credentials: {e}")
    
    return client_id, client_secret


def create_reddit_api(script_dir: Optional[str] = None) -> Optional[RedditAPI]:
    client_id, client_secret = load_reddit_credentials(script_dir)
    
    if not client_id or not client_secret:
        return None
    
    auth = RedditAuth(client_id, client_secret)
    return RedditAPI(auth)
