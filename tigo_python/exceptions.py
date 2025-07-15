# tigo_python/exceptions.py
import httpx
from typing import Optional, Dict, Any

class TigoAPIError(Exception):
    """Exception raised for Tigo API errors."""
    
    def __init__(self, response: httpx.Response, context: Optional[str] = None):
        self.response = response
        self.status_code = response.status_code
        self.url = str(response.url)
        self.context = context
        
        try:
            self.error_data = response.json()
            error_msg = self.error_data.get('message', str(self.error_data))
        except Exception:
            error_msg = response.text[:200]  # Limit error text length
        
        message_parts = [f"Tigo API Error {self.status_code}"]
        if context:
            message_parts.append(f"({context})")
        message_parts.append(f": {error_msg}")
        
        message = " ".join(message_parts)
        super().__init__(message)

class TigoAuthenticationError(TigoAPIError):
    """Exception raised for authentication failures."""
    pass

class TigoRateLimitError(TigoAPIError):
    """Exception raised when API rate limits are exceeded."""
    pass