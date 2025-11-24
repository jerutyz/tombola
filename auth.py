# auth.py - Authentication utilities
import os
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
SCRAPE_API_KEY = os.getenv('SCRAPE_API_KEY')

def require_api_key(f):
    """
    Decorator to require API key authentication.
    
    Usage:
        @app.route('/api/protected')
        @require_api_key
        def protected_route():
            return "Protected content"
    
    Client must include header:
        X-API-Key: your_api_key_here
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from request headers
        api_key = request.headers.get('X-API-Key')
        
        # Check if API key exists and matches
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key is missing. Include X-API-Key header.'
            }), 401
        
        if api_key != SCRAPE_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Invalid API key.'
            }), 403
        
        # API key is valid, proceed with the route
        return f(*args, **kwargs)
    
    return decorated_function
