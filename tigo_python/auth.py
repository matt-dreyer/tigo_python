# tigo_python/auth.py
import httpx
import base64
from typing import Optional
from .exceptions import TigoAuthenticationError

class TigoAuthenticator:
    def __init__(self, username: str, password: str):
        if not username or not password:
            raise ValueError("Username and password are required")
            
        self.username = username
        self.password = password
        self._auth_token: Optional[str] = None
        self._user_id: Optional[int] = None
        self._login()
    
    def _login(self):
        """Login and get auth token."""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {"Authorization": f"Basic {encoded_credentials}"}
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    "https://api2.tigoenergy.com/api/v3/users/login",
                    headers=headers
                )
                
                if response.status_code == 401:
                    raise TigoAuthenticationError(response, "Invalid credentials")
                elif response.status_code == 429:
                    raise TigoAuthenticationError(response, "Rate limit exceeded")
                elif response.status_code != 200:
                    raise TigoAuthenticationError(response, "Login failed")
                
                data = response.json()
                
                # Handle different response formats
                if "user" in data:
                    user_data = data["user"]
                    self._auth_token = user_data.get("auth")
                    self._user_id = user_data.get("user_id")
                else:
                    # Fallback for different response format
                    self._auth_token = data.get("auth") or data.get("token")
                    self._user_id = data.get("user_id") or data.get("id")
                
                if not self._auth_token:
                    raise TigoAuthenticationError(response, "No auth token in response")
                    
        except httpx.RequestError as e:
            raise TigoAuthenticationError(None, f"Network error during login: {e}")
    
    def get_headers(self) -> dict:
        """Get authorization headers."""
        if not self._auth_token:
            raise ValueError("Not authenticated. Auth token is missing.")
        return {"Authorization": f"Bearer {self._auth_token}"}
    
    def get_user_id(self) -> int:
        """Get the authenticated user ID."""
        if self._user_id is None:
            raise ValueError("User ID not available")
        return self._user_id
    
    def is_authenticated(self) -> bool:
        """Check if authentication is valid."""
        return self._auth_token is not None