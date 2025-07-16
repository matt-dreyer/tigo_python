# tigo_python/auth.py
import httpx
import base64
import time
from typing import Optional
from .exceptions import TigoAuthenticationError, TigoConnectionError

class TigoAuthenticator:
    """Handles authentication and token management for Tigo API."""
    
    BASE_URL = "https://api2.tigoenergy.com/api/v3"
    
    def __init__(self, username: str, password: str, auto_refresh: bool = True):
        if not username or not password:
            raise ValueError("Username and password are required")
            
        self.username = username
        self.password = password
        self.auto_refresh = auto_refresh
        
        self._auth_token: Optional[str] = None
        self._user_id: Optional[int] = None
        self._token_expires_at: Optional[float] = None
        
        # Authenticate immediately
        self._authenticate()
    
    def _authenticate(self):
        """Perform authentication and store credentials."""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {"Authorization": f"Basic {encoded_credentials}"}
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.BASE_URL}/users/login",
                    headers=headers
                )
                
                if response.status_code == 401:
                    raise TigoAuthenticationError("Invalid username or password", response)
                elif response.status_code == 429:
                    raise TigoAuthenticationError("Rate limit exceeded during authentication", response)
                elif response.status_code != 200:
                    raise TigoAuthenticationError(f"Authentication failed with status {response.status_code}", response)
                
                data = response.json()
                
                # Handle different response formats
                if "user" in data:
                    user_data = data["user"]
                    self._auth_token = user_data.get("auth")
                    self._user_id = user_data.get("user_id")
                else:
                    self._auth_token = data.get("auth") or data.get("token")
                    self._user_id = data.get("user_id") or data.get("id")
                
                if not self._auth_token:
                    raise TigoAuthenticationError("No authentication token received", response)
                
                # Set token expiration (assume 1 hour if not provided)
                self._token_expires_at = time.time() + 3600
                    
        except httpx.RequestError as e:
            raise TigoConnectionError(f"Network error during authentication: {e}")
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is valid and not expired."""
        if not self._auth_token:
            return False
        
        if self._token_expires_at and time.time() >= self._token_expires_at - 300:  # 5 min buffer
            return False
            
        return True
    
    def _ensure_authenticated(self):
        """Ensure we have a valid authentication token."""
        if not self._is_token_valid():
            if self.auto_refresh:
                self._authenticate()
            else:
                raise TigoAuthenticationError("Authentication token expired and auto_refresh is disabled")
    
    def get_headers(self) -> dict:
        """Get authorization headers for API requests."""
        self._ensure_authenticated()
        return {"Authorization": f"Bearer {self._auth_token}"}
    
    def get_user_id(self) -> int:
        """Get the authenticated user ID."""
        self._ensure_authenticated()
        if self._user_id is None:
            raise TigoAuthenticationError("User ID not available")
        return self._user_id
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_token_valid()
    
    def logout(self):
        """Clear authentication state."""
        self._auth_token = None
        self._user_id = None
        self._token_expires_at = None
