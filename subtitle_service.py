import os
import logging
import time
import xmlrpc.client
import gzip
import base64
from typing import Dict, List, Optional

class SubtitleService:
    """Service for interacting with OpenSubtitles.org XML-RPC API"""
    
    def __init__(self):
        self.base_url = "https://api.opensubtitles.org/xml-rpc"
        self.username = os.getenv("OPENSUBTITLES_USERNAME", "scara78")
        self.password = os.getenv("OPENSUBTITLES_PASSWORD", "scara78")
        self.user_agent = "SubtitleAPI v1.0"
        self.token = None
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests for XML-RPC
        
        # Initialize XML-RPC client
        try:
            self.server = xmlrpc.client.ServerProxy(self.base_url)
            logging.info("OpenSubtitles.org XML-RPC client initialized")
        except Exception as e:
            logging.error(f"Failed to initialize XML-RPC client: {e}")
            self.server = None
        
        if not self.username or not self.password:
            logging.warning("OpenSubtitles credentials not set - using demo mode")
        else:
            logging.info("OpenSubtitles.org credentials configured")
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _login(self):
        """Login to OpenSubtitles.org to get session token"""
        if not self.server:
            return False
            
        if not self.username or not self.password:
            logging.error("Username and password required for login")
            return False
        
        try:
            self._wait_for_rate_limit()
            
            response = self.server.LogIn(self.username, self.password, 'en', self.user_agent)
            
            if response['status'] == '200 OK':
                self.token = response['token']
                logging.info("Successfully logged in to OpenSubtitles.org")
                return True
            else:
                logging.error(f"Login failed: {response.get('status', 'Unknown error')}")
                return False
                
        except Exception as e:
            logging.error(f"Login error: {e}")
            return False
    
    def _ensure_logged_in(self):
        """Ensure we have a valid session token"""
        if not self.token:
            return self._login()
        return True
    
    def search_subtitles(self, params: Dict) -> List[Dict]:
        """Search for subtitles using OpenSubtitles.org XML-RPC API"""
        if not self.server:
            logging.error("XML-RPC server not available")
            return []
        
        if not self._ensure_logged_in():
            logging.error("Failed to login to OpenSubtitles.org")
            return []
        
        try:
            self._wait_for_rate_limit()
            
            # Convert parameters to OpenSubtitles.org format
            search_params = []
            search_data = {}
            
            if params.get('imdb_id'):
                # Remove 'tt' prefix if present
                imdb_id = params['imdb_id'].replace('tt', '')
                search_data['imdbid'] = imdb_id
            
            if params.get('query'):
                search_data['query'] = params['query']
            
            if params.get('moviehash'):
                search_data['moviehash'] = params['moviehash']
            
            if params.get('languages'):
                # Convert language codes (e.g., 'en,es' to format expected by API)
                languages = params['languages'].split(',')
                if len(languages) == 1:
                    search_data['sublanguageid'] = languages[0].strip()
                else:
                    search_data['sublanguageid'] = ','.join(lang.strip() for lang in languages)
            
            search_params.append(search_data)
            
            # Perform search
            response = self.server.SearchSubtitles(self.token, search_params)
            
            if response['status'] != '200 OK':
                logging.error(f"Search failed: {response.get('status', 'Unknown error')}")
                return []
            
            # Convert response to our standard format
            results = []
            subtitle_data = response.get('data', [])
            
            # Limit results to prevent timeouts
            for subtitle in subtitle_data[:10]:
                result = {
                    'id': subtitle.get('IDSubtitleFile'),
                    'attributes': {
                        'language': subtitle.get('SubLanguageID'),
                        'release': subtitle.get('SubFileName'),
                        'hearing_impaired': subtitle.get('SubHearingImpaired') == '1',
                        'download_count': int(subtitle.get('SubDownloadsCnt', 0)),
                        'rating': float(subtitle.get('SubRating', 0.0)) if subtitle.get('SubRating') else None,
                        'format': 'srt',  # OpenSubtitles.org primarily provides SRT
                        'file_id': subtitle.get('IDSubtitleFile'),
                        'movie_name': subtitle.get('MovieName'),
                        'year': subtitle.get('MovieYear'),
                        'imdb_id': subtitle.get('IDMovieImdb'),
                        'file_size': subtitle.get('SubSize'),
                        'encoding': subtitle.get('SubEncoding'),
                        'download_link': subtitle.get('SubDownloadLink')
                    }
                }
                results.append(result)
            
            logging.info(f"Found {len(results)} subtitles")
            return results
            
        except Exception as e:
            logging.error(f"Search error: {e}")
            return []
    
    def get_download_link(self, file_id: str) -> Optional[Dict]:
        """Get download link for a subtitle file"""
        if not self.server:
            return None
            
        if not self._ensure_logged_in():
            return None
        
        try:
            self._wait_for_rate_limit()
            
            # Get download link
            response = self.server.DownloadSubtitles(self.token, [file_id])
            
            if response['status'] != '200 OK':
                logging.error(f"Download link request failed: {response.get('status')}")
                return None
            
            if not response.get('data'):
                return None
            
            subtitle_data = response['data'][0]
            
            # Decode the subtitle content
            encoded_data = subtitle_data.get('data')
            if encoded_data:
                try:
                    # Decode base64 and decompress gzip
                    decoded_data = base64.b64decode(encoded_data)
                    subtitle_content = gzip.decompress(decoded_data).decode('utf-8')
                    
                    return {
                        'link': None,  # Content is provided directly
                        'content': subtitle_content,
                        'file_name': f"subtitle_{file_id}.srt",
                        'encoding': 'utf-8'
                    }
                except Exception as e:
                    logging.error(f"Failed to decode subtitle data: {e}")
                    return None
            
            return None
            
        except Exception as e:
            logging.error(f"Download error: {e}")
            return None
    
    def logout(self):
        """Logout from OpenSubtitles.org"""
        if self.server and self.token:
            try:
                self._wait_for_rate_limit()
                self.server.LogOut(self.token)
                self.token = None
                logging.info("Logged out from OpenSubtitles.org")
            except Exception as e:
                logging.error(f"Logout error: {e}")