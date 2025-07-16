# tigo_python/exceptions.py
import httpx
from typing import Optional, Dict, Any

class TigoAPIError(Exception):
    """Base exception for Tigo API errors."""
    
    def __init__(self, message: str, response: Optional[httpx.Response] = None, context: Optional[str] = None):
        self.response = response
        self.status_code = response.status_code if response else None
        self.url = str(response.url) if response else None
        self.context = context
        
        if response and not message:
            try:
                error_data = response.json()
                message = error_data.get('message', str(error_data))
            except Exception:
                message = response.text[:200]
        
        if context:
            message = f"{context}: {message}"
            
        super().__init__(message)

class TigoAuthenticationError(TigoAPIError):
    """Exception raised for authentication failures."""
    pass

class TigoRateLimitError(TigoAPIError):
    """Exception raised when API rate limits are exceeded."""
    pass

class TigoConnectionError(TigoAPIError):
    """Exception raised for connection-related errors."""
    pass
