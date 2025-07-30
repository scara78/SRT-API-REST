import os
import requests
import json
import logging
import time
from typing import Dict, List, Optional

class SubtitleService:
    """Service for interacting with OpenSubtitles.com REST API"""
    
    def __init__(self):
        self.base_url = "https://api.opensubtitles.com/api/v1"
        self.api_key = os.getenv("OPENSUBTITLES_API_KEY", "xFG0wOKOVHj13KUt1hS5eVWK6MWyeKsx")
        self.username = os.getenv("OPENSUBTITLES_USERNAME", "scara78")
        self.password = os.getenv("OPENSUBTITLES_PASSWORD", "scara78")
        self.jwt_token = None
        self.token_expires_at = 0
        
        # Rate limiting - reduced for better performance
        self.last_request_time = 0
        self.min_request_interval = 0.3  # Minimum 0.3 seconds between requests
        
        if not self.api_key or self.api_key == "demo":
            logging.warning("OPENSUBTITLES_API_KEY not set - using demo mode")
        else:
            logging.info("OpenSubtitles API credentials configured")
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _get_headers(self, include_auth=False):
        """Get request headers with API key and optionally JWT token"""
        headers = {
            'Api-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'SubtitleAPI/1.0'
        }
        
        if include_auth and self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        return headers
    
    def _login(self):
        """Login to get JWT token for downloads"""
        if not self.username or not self.password:
            logging.error("Username and password required for login")
            return False
        
        # Check if token is still valid (with 5 minute buffer)
        if self.jwt_token and time.time() < (self.token_expires_at - 300):
            return True
        
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/login"
            data = {
                'username': self.username,
                'password': self.password
            }
            
            response = requests.post(
                url,
                data=json.dumps(data),
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.jwt_token = result.get('token')
                # Tokens typically expire after 24 hours
                self.token_expires_at = time.time() + (24 * 3600)
                logging.info("Successfully logged in to OpenSubtitles")
                return True
            else:
                logging.error(f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Login error: {e}")
            return False
    
    def search_subtitles(self, search_params: Dict) -> List[Dict]:
        """
        Search for subtitles using OpenSubtitles API
        
        Args:
            search_params: Dictionary with search parameters
                - imdb_id: IMDB movie ID
                - query: Text search
                - languages: Language codes
                - moviehash: File hash
        
        Returns:
            List of subtitle results
        """
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/subtitles"
            
            # Convert search_params to query parameters
            params = {}
            for key, value in search_params.items():
                if value:
                    params[key] = value
            
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', [])
            elif response.status_code == 429:
                logging.warning("Rate limit exceeded")
                # Check for Retry-After header
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    logging.info(f"Retry after {retry_after} seconds")
                return []
            else:
                logging.error(f"Search failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Search error: {e}")
            return []
    
    def get_download_link(self, file_id: int) -> Optional[Dict]:
        """
        Get direct download link for a subtitle file
        
        Args:
            file_id: The file ID from search results
        
        Returns:
            Dictionary with download information or None
        """
        try:
            # Login first to get JWT token
            if not self._login():
                logging.error("Login required for downloads but failed")
                return None
            
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/download"
            data = {'file_id': file_id}
            
            response = requests.post(
                url,
                data=json.dumps(data),
                headers=self._get_headers(include_auth=True),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logging.error("Authentication failed - token may be expired")
                # Try to login again
                self.jwt_token = None
                if self._login():
                    # Retry the request
                    response = requests.post(
                        url,
                        data=json.dumps(data),
                        headers=self._get_headers(include_auth=True),
                        timeout=30
                    )
                    if response.status_code == 200:
                        return response.json()
                return None
            elif response.status_code == 429:
                logging.warning("Rate limit exceeded for downloads")
                return None
            else:
                logging.error(f"Download failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Download error: {e}")
            return None
    
    def get_latest_subtitles(self, languages: str = "en") -> List[Dict]:
        """
        Get latest subtitles
        
        Args:
            languages: Comma-separated language codes
        
        Returns:
            List of latest subtitle results
        """
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/discover/latest"
            params = {'languages': languages}
            
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', [])
            else:
                logging.error(f"Latest subtitles failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Latest subtitles error: {e}")
            return []
