import os
import logging
import signal
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from subtitle_service import SubtitleService
from format_converter import FormatConverter
from cache_manager import CacheManager

# Timeout handler for preventing worker timeouts
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Request timeout")

def with_timeout(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Disable alarm
                return result
            except TimeoutException:
                signal.alarm(0)  # Disable alarm
                return jsonify({
                    'error': 'Request timeout',
                    'message': 'The request took too long to process. Try reducing the number of results or using a more specific search.'
                }), 408
        return wrapper
    return decorator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Enable CORS for all routes
CORS(app)

# Initialize services
subtitle_service = SubtitleService()
format_converter = FormatConverter()
cache_manager = CacheManager()

@app.route('/')
def index():
    """Main page with API documentation and testing interface"""
    return render_template('index.html')

@app.route('/api/v1/search', methods=['GET'])
@with_timeout(25)  # 25 second timeout to prevent worker timeouts
def search_subtitles():
    """
    Search for subtitles by various criteria
    Query parameters:
    - imdb_id: IMDB movie ID (e.g., tt0120338)
    - query: Text search query
    - languages: Comma-separated language codes (e.g., en,es,fr)
    - moviehash: File hash
    - format: Preferred format (srt or vtt, default: srt)
    """
    try:
        # Get query parameters
        imdb_id = request.args.get('imdb_id')
        query = request.args.get('query')
        languages = request.args.get('languages', 'en')
        moviehash = request.args.get('moviehash')
        preferred_format = request.args.get('format', 'srt').lower()
        
        # Validate input
        if not any([imdb_id, query, moviehash]):
            return jsonify({
                'error': 'At least one search parameter is required: imdb_id, query, or moviehash'
            }), 400
        
        if preferred_format not in ['srt', 'vtt']:
            return jsonify({
                'error': 'Format must be either "srt" or "vtt"'
            }), 400
        
        # Create cache key
        cache_key = f"search:{imdb_id}:{query}:{languages}:{moviehash}:{preferred_format}"
        
        # Check cache first
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logging.info(f"Cache hit for key: {cache_key}")
            return jsonify(cached_result)
        
        # Search subtitles
        search_params = {
            'imdb_id': imdb_id,
            'query': query,
            'languages': languages,
            'moviehash': moviehash
        }
        
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        subtitles = subtitle_service.search_subtitles(search_params)
        
        if not subtitles:
            # Check if this is a demo/authentication issue
            if not subtitle_service.api_key or subtitle_service.api_key == "demo":
                return jsonify({
                    'error': 'OpenSubtitles API authentication required',
                    'message': 'Please provide valid OPENSUBTITLES_API_KEY, OPENSUBTITLES_USERNAME, and OPENSUBTITLES_PASSWORD',
                    'demo_response': {
                        'results': [],
                        'total_count': 0,
                        'search_params': search_params,
                        'format': preferred_format,
                        'note': 'This would contain subtitle results with valid API credentials'
                    }
                }), 200
            else:
                return jsonify({
                    'error': 'No subtitles found for the given criteria',
                    'results': []
                }), 404
        
        # Process results for OpenSubtitles.org format
        processed_results = []
        
        for subtitle in subtitles:
            try:
                attributes = subtitle.get('attributes', {})
                original_format = 'srt'  # OpenSubtitles.org provides SRT
                
                # Create direct link to our content endpoint instead of .gz link
                file_id = attributes.get('file_id')
                base_url = request.url_root.rstrip('/')
                download_link = f"{base_url}/api/v1/content/{file_id}?format={preferred_format}"
                
                result = {
                    'id': subtitle.get('id'),
                    'attributes': {
                        'language': attributes.get('language'),
                        'release': attributes.get('release'),
                        'hearing_impaired': attributes.get('hearing_impaired'),
                        'download_count': attributes.get('download_count'),
                        'rating': attributes.get('rating'),
                        'format': preferred_format,
                        'file_id': file_id,
                        'movie_name': attributes.get('movie_name'),
                        'year': attributes.get('year'),
                        'imdb_id': attributes.get('imdb_id'),
                        'file_size': attributes.get('file_size'),
                        'encoding': attributes.get('encoding')
                    },
                    'download_link': download_link,
                    'file_name': f"{attributes.get('movie_name', 'subtitle')}.{preferred_format}"
                }
                processed_results.append(result)
                
            except Exception as e:
                logging.error(f"Error processing subtitle: {e}")
                continue
        
        response_data = {
            'results': processed_results,
            'total_count': len(processed_results),
            'search_params': search_params,
            'format': preferred_format
        }
        
        # Cache the result for 1 hour
        cache_manager.set(cache_key, response_data, 3600)
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Search error: {e}")
        return jsonify({
            'error': f'Search failed: {str(e)}'
        }), 500

@app.route('/api/v1/download/<int:file_id>', methods=['GET'])
def get_download_link(file_id):
    """
    Get direct download link for a specific subtitle file
    Query parameters:
    - format: Desired format (srt or vtt, default: srt)
    """
    try:
        preferred_format = request.args.get('format', 'srt').lower()
        
        if preferred_format not in ['srt', 'vtt']:
            return jsonify({
                'error': 'Format must be either "srt" or "vtt"'
            }), 400
        
        # Check cache first
        cache_key = f"download:{file_id}:{preferred_format}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return jsonify(cached_result)
        
        # Get subtitle content from OpenSubtitles
        download_info = subtitle_service.get_download_link(str(file_id))
        if not download_info:
            return jsonify({
                'error': 'Failed to get subtitle content'
            }), 500
        
        # Get the decompressed content
        subtitle_content = download_info.get('content')
        if not subtitle_content:
            return jsonify({
                'error': 'No subtitle content available'
            }), 404
        
        # Convert format if needed
        if preferred_format == 'vtt':
            subtitle_content = format_converter.convert_content(subtitle_content, 'srt', 'vtt')
        
        # Create direct link to our content endpoint
        base_url = request.url_root.rstrip('/')
        direct_link = f"{base_url}/api/v1/content/{file_id}?format={preferred_format}"
        
        response_data = {
            'download_link': direct_link,
            'file_name': download_info.get('file_name', f'subtitle_{file_id}.{preferred_format}'),
            'format': preferred_format,
            'file_id': str(file_id),
            'content': subtitle_content  # Include content for immediate use
        }
        
        # Cache the content for 1 hour
        cache_manager.set(f"content:{file_id}:srt", download_info.get('content'), 3600)
        if preferred_format == 'vtt':
            cache_manager.set(f"content:{file_id}:vtt", subtitle_content, 3600)
        
        # Cache response for 30 minutes
        cache_manager.set(cache_key, response_data, 1800)
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Download error: {e}")
        return jsonify({
            'error': f'Download failed: {str(e)}'
        }), 500

@app.route('/api/v1/content/<int:file_id>', methods=['GET'])
def get_subtitle_content(file_id):
    """
    Serve raw subtitle content (SRT/VTT) with proper headers for direct use
    """
    try:
        preferred_format = request.args.get('format', 'srt').lower()
        
        # Check cache first
        cache_key = f"content:{file_id}:{preferred_format}"
        cached_content = cache_manager.get(cache_key)
        
        if not cached_content:
            # If not in cache, try to get it from OpenSubtitles
            download_info = subtitle_service.get_download_link(str(file_id))
            if not download_info or not download_info.get('content'):
                return "Subtitle not found", 404
            
            content = download_info.get('content')
            
            # Convert format if needed
            if preferred_format == 'vtt':
                content = format_converter.convert_content(content, 'srt', 'vtt')
            
            # Cache it
            cache_manager.set(cache_key, content, 3600)
            cached_content = content
        
        # Set appropriate headers for subtitle files
        headers = {
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Disposition': f'attachment; filename="subtitle_{file_id}.{preferred_format}"',
            'Access-Control-Allow-Origin': '*'
        }
        
        return cached_content, 200, headers
        
    except Exception as e:
        logging.error(f"Content serving error: {e}")
        return f"Error serving content: {str(e)}", 500

@app.route('/api/v1/convert', methods=['POST'])
def convert_format():
    """
    Convert subtitle format from SRT to VTT or vice versa
    Expects JSON payload with 'content' and 'from_format' and 'to_format'
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON payload required'}), 400
        
        content = data.get('content')
        from_format = data.get('from_format', '').lower()
        to_format = data.get('to_format', '').lower()
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if from_format not in ['srt', 'vtt'] or to_format not in ['srt', 'vtt']:
            return jsonify({'error': 'Formats must be either "srt" or "vtt"'}), 400
        
        if from_format == to_format:
            return jsonify({
                'converted_content': content,
                'from_format': from_format,
                'to_format': to_format
            })
        
        # Convert format
        converted_content = format_converter.convert_content(content, from_format, to_format)
        
        return jsonify({
            'converted_content': converted_content,
            'from_format': from_format,
            'to_format': to_format
        })
        
    except Exception as e:
        logging.error(f"Conversion error: {e}")
        return jsonify({
            'error': f'Conversion failed: {str(e)}'
        }), 500

@app.route('/api/v1/demo', methods=['GET'])
def demo_response():
    """Get demo response showing expected JSON structure with sample data"""
    imdb_id = request.args.get('imdb_id', 'tt0120338')
    preferred_format = request.args.get('format', 'srt')
    languages = request.args.get('languages', 'en')
    
    # Sample response structure that would be returned with real API access
    sample_response = {
        'results': [
            {
                'id': '5274788',
                'attributes': {
                    'language': 'en',
                    'release': 'Titanic.1997.BluRay.x264',
                    'hearing_impaired': False,
                    'download_count': 12543,
                    'rating': 8.5,
                    'format': preferred_format,
                    'file_id': 5274788
                },
                'download_link': f'https://example.com/subtitle.{preferred_format}',
                'file_name': f'titanic.{preferred_format}'
            },
            {
                'id': '5274789',
                'attributes': {
                    'language': 'en',
                    'release': 'Titanic.1997.HDTV.x264',
                    'hearing_impaired': True,
                    'download_count': 8421,
                    'rating': 7.8,
                    'format': preferred_format,
                    'file_id': 5274789
                },
                'download_link': f'https://example.com/subtitle-hi.{preferred_format}',
                'file_name': f'titanic-hi.{preferred_format}'
            }
        ],
        'total_count': 2,
        'search_params': {
            'imdb_id': imdb_id,
            'languages': languages
        },
        'format': preferred_format,
        'note': 'This is sample data - real API requires OpenSubtitles credentials'
    }
    
    return jsonify(sample_response)

@app.route('/api/v1/status', methods=['GET'])
def api_status():
    """Get API status and configuration"""
    has_credentials = bool(subtitle_service.username and subtitle_service.password)
    
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'opensubtitles_api': 'https://api.opensubtitles.org/xml-rpc',
        'supported_formats': ['srt', 'vtt'],
        'cache_enabled': True,
        'rate_limiting': True,
        'authentication': {
            'credentials_configured': has_credentials,
            'demo_mode': not has_credentials,
            'server_available': subtitle_service.server is not None
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
