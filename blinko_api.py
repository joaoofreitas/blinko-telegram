#!/usr/bin/env python3
"""
Blinko API Client - Simple HTTP client for Blinko note creation

Features:
- Create notes via /note/upsert endpoint
- Token validation via GET request
- Handles SSL verification and timeouts
- Supports both note types (0=note, 1=blinko)
"""

import requests
import logging
from typing import Dict, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class BlinkoAPI:
    """Simple Blinko API client for note creation."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BlinkoTelegramBot/1.0'
        })
        # Disable SSL verification for self-signed certificates
        # In production, you should use proper SSL certificates
        self.session.verify = False
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def create_note(self, token: str, content: str, note_type: int = 0) -> Dict[str, Any]:
        """Create a new note using the upsert endpoint."""
        if not content or not content.strip():
            return {
                'success': False,
                'error': 'validation',
                'message': 'Note content cannot be empty'
            }
        
        note_data = {
            'content': content.strip(),
            'type': note_type
        }
        
        try:
            # Ensure base_url ends with / and endpoint doesn't start with /
            base_url = self.base_url.rstrip('/') + '/'
            endpoint = 'note/upsert'
            url = urljoin(base_url, endpoint)
            
            headers = {'Authorization': f'Bearer {token}'}
            
            response = self.session.post(
                url=url,
                headers=headers,
                json=note_data,
                timeout=30
            )
            
            logger.info(f"API POST /note/upsert - Status: {response.status_code}")
            
            if response.status_code == 401:
                return {
                    'success': False,
                    'error': 'unauthorized',
                    'message': 'Invalid or expired token. Please reconfigure with /configure'
                }
            
            if response.status_code >= 400:
                return {
                    'success': False,
                    'error': 'api_error',
                    'message': f'API error: {response.status_code}',
                    'status_code': response.status_code
                }
            
            result = response.json()
            return {
                'success': True,
                'data': result,
                'note_id': result.get('id')
            }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout making request to Blinko API")
            return {
                'success': False,
                'error': 'timeout',
                'message': 'Request timed out. Please try again.'
            }
        except requests.exceptions.ConnectionError:
            logger.error("Connection error making request to Blinko API")
            return {
                'success': False,
                'error': 'connection',
                'message': 'Failed to connect to Blinko server. Please check your configuration.'
            }
        except Exception as e:
            logger.error(f"Unexpected error making request to Blinko API: {e}")
            return {
                'success': False,
                'error': 'unexpected',
                'message': f'Unexpected error: {str(e)}'
            }
    
    def update_note(self, token: str, note_id: str, content: str, note_type: int = 0) -> Dict[str, Any]:
        """Update an existing note using the upsert endpoint with note ID."""
        if not content or not content.strip():
            return {
                'success': False,
                'error': 'validation',
                'message': 'Note content cannot be empty'
            }
        
        note_data = {
            'id': note_id,
            'content': content.strip(),
            'type': note_type
        }
        
        try:
            # Ensure base_url ends with / and endpoint doesn't start with /
            base_url = self.base_url.rstrip('/') + '/'
            endpoint = 'note/upsert'
            url = urljoin(base_url, endpoint)
            
            headers = {'Authorization': f'Bearer {token}'}
            
            response = self.session.post(
                url=url,
                headers=headers,
                json=note_data,
                timeout=30
            )
            
            logger.info(f"API POST /note/upsert (update) - Status: {response.status_code}")
            
            if response.status_code == 401:
                return {
                    'success': False,
                    'error': 'unauthorized',
                    'message': 'Invalid or expired token. Please reconfigure with /configure'
                }
            
            if response.status_code >= 400:
                return {
                    'success': False,
                    'error': 'api_error',
                    'message': f'API error: {response.status_code}',
                    'status_code': response.status_code
                }
            
            result = response.json()
            return {
                'success': True,
                'data': result,
                'note_id': result.get('id', note_id)
            }
                
        except requests.exceptions.Timeout:
            logger.error("Timeout making request to Blinko API")
            return {
                'success': False,
                'error': 'timeout',
                'message': 'Request timed out. Please try again.'
            }
        except requests.exceptions.ConnectionError:
            logger.error("Connection error making request to Blinko API")
            return {
                'success': False,
                'error': 'connection',
                'message': 'Failed to connect to Blinko server. Please check your configuration.'
            }
        except Exception as e:
            logger.error(f"Unexpected error making request to Blinko API: {e}")
            return {
                'success': False,
                'error': 'unexpected',
                'message': f'Unexpected error: {str(e)}'
            }
    
    def test_token(self, token: str) -> Dict[str, Any]:
        """Test if a token is valid by making a simple request."""
        try:
            # Try to access the API with the token without creating a note
            # This is a simple way to validate the token
            headers = {'Authorization': f'Bearer {token}'}
            
            # Use a simple GET request to test authentication
            # If this endpoint doesn't exist, we'll catch the error appropriately
            base_url = self.base_url.rstrip('/') + '/'
            
            response = self.session.get(
                url=urljoin(base_url, 'note'),  # Try to list notes (common endpoint)
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                return {
                    'success': False,
                    'error': 'unauthorized',
                    'message': 'Invalid or expired token'
                }
            
            # If we get any response that's not unauthorized, consider token valid
            # Even 403 (forbidden) means the token is recognized
            if response.status_code in [200, 403]:
                return {
                    'success': True,
                    'message': 'Token is valid'
                }
            
            # For other status codes, still consider it valid if not unauthorized
            return {
                'success': True,
                'message': 'Token appears valid (authentication successful)'
            }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'timeout',
                'message': 'Request timed out. Server may be unavailable.'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'connection',
                'message': 'Failed to connect to Blinko server.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'unexpected',
                'message': f'Unexpected error: {str(e)}'
            }
