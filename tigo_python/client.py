# tigo_python/client.py
import os
import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Any
from io import StringIO
import logging
from contextlib import contextmanager

from .auth import TigoAuthenticator
from .exceptions import TigoAPIError, TigoRateLimitError, TigoConnectionError

class TigoClient:
    """
    Modern Python client for the Tigo Energy API.
    
    Provides clean access to Tigo Energy's monitoring API with proper
    connection management and error handling.
    """
    
    BASE_URL = "https://api2.tigoenergy.com/api/v3"
    DEFAULT_TIMEOUT = 30.0
    
    # API Limits
    SAFE_LIMIT_MINUTES = 20150
    MAX_DAYS_REQUEST = 365
    MINUTE_LEVEL_THRESHOLD = 100
    
    # Analysis Constants
    DAYLIGHT_START_HOUR = 6
    DAYLIGHT_END_HOUR = 20
    MIN_PRODUCTION_THRESHOLD = 0.05
    MAX_PANELS_TO_ANALYZE = 10
    PANEL_VARIATION_RANGE = (0.85, 1.15)

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, 
                 timeout: float = DEFAULT_TIMEOUT, auto_refresh: bool = True):
        """
        Initialize TigoClient.
        
        Args:
            username: Tigo username (or from TIGO_USERNAME env var)
            password: Tigo password (or from TIGO_PASSWORD env var)
            timeout: Request timeout in seconds
            auto_refresh: Automatically refresh authentication tokens
        """
        self.logger = logging.getLogger(__name__)
        
        # Get credentials
        username = username or os.getenv("TIGO_USERNAME")
        password = password or os.getenv("TIGO_PASSWORD")
        
        if not username or not password:
            raise ValueError(
                "Username and password required. Either pass them directly or set "
                "TIGO_USERNAME and TIGO_PASSWORD environment variables."
            )
        
        # Initialize authenticator
        self.authenticator = TigoAuthenticator(username, password, auto_refresh)
        
        # Create persistent HTTP client
        self._client: Optional[httpx.Client] = None
        self.timeout = timeout
        self._create_client()

    def _create_client(self):
        """Create or recreate the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
        
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=self.timeout,
            headers=self.authenticator.get_headers()
        )

    def _ensure_client_ready(self):
        """Ensure the HTTP client is ready for requests."""
        if not self._client or self._client.is_closed:
            self._create_client()
        else:
            # Update headers in case token was refreshed
            self._client.headers.update(self.authenticator.get_headers())

    def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make HTTP request with proper error handling."""
        self._ensure_client_ready()
        
        try:
            response = getattr(self._client, method.lower())(endpoint, **kwargs)
            
            if response.status_code == 401:
                # Try to refresh authentication once
                self.authenticator._authenticate()
                self._client.headers.update(self.authenticator.get_headers())
                response = getattr(self._client, method.lower())(endpoint, **kwargs)
                
                if response.status_code == 401:
                    raise TigoAuthenticationError("Authentication failed", response)
            
            elif response.status_code == 429:
                raise TigoRateLimitError("API rate limit exceeded", response)
            
            elif response.status_code >= 400:
                raise TigoAPIError(f"API request failed with status {response.status_code}", response)
            
            return response
            
        except httpx.RequestError as e:
            raise TigoConnectionError(f"Network error: {e}")

    # Core HTTP methods
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request and return JSON."""
        response = self._make_request('GET', endpoint, **kwargs)
        return response.json()

    def get_raw(self, endpoint: str, **kwargs) -> str:
        """Make GET request and return raw text."""
        response = self._make_request('GET', endpoint, **kwargs)
        return response.text

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request and return JSON."""
        if data:
            kwargs['json'] = data
        response = self._make_request('POST', endpoint, **kwargs)
        return response.json()

    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client and clean up resources."""
        if self._client and not self._client.is_closed:
            self._client.close()
            self.logger.debug("HTTP client closed")

    # User API methods
    def get_user(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user information."""
        if user_id is None:
            user_id = self.authenticator.get_user_id()
        return self.get(f"/users/{user_id}")

    def logout(self) -> Dict[str, Any]:
        """Logout current user."""
        try:
            result = self.get("/users/logout")
            self.authenticator.logout()
            return result
        except Exception as e:
            self.authenticator.logout()  # Clear local state anyway
            raise

    # System API methods
    def list_systems(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """List accessible systems."""
        params = {"page": page, "limit": limit}
        return self.get("/systems", params=params)

    def get_system(self, system_id: int) -> Dict[str, Any]:
        """Get system details."""
        return self.get("/systems/view", params={"id": system_id})

    def get_system_layout(self, system_id: int) -> Dict[str, Any]:
        """Get system electrical layout."""
        return self.get("/systems/layout", params={"id": system_id})

    def get_sources(self, system_id: int) -> Dict[str, Any]:
        """Get system sources."""
        return self.get("/sources/system", params={"system_id": system_id})

    def get_objects(self, system_id: int) -> Dict[str, Any]:
        """Get system objects."""
        return self.get("/objects/system", params={"system_id": system_id})

    def get_object_types(self) -> Dict[str, Any]:
        """Get available object types."""
        return self.get("/objects/types")

    # Data API methods
    def get_summary(self, system_id: int) -> Dict[str, Any]:
        """Get system summary data."""
        return self.get("/data/summary", params={"system_id": system_id})

    def get_aggregate_data(
        self, 
        system_id: int, 
        start: str, 
        end: str, 
        level: str = "hour",
        param: str = "Pin",
        header: str = "id",
        sensors: bool = True,
        object_ids: Optional[str] = None,
        return_dataframe: bool = True
    ) -> Union[str, pd.DataFrame]:
        """Get aggregate data."""
        params = {
            "system_id": system_id,
            "start": start,
            "end": end,
            "level": level,
            "param": param,
            "header": header,
            "sensors": str(sensors).lower()
        }
        if object_ids:
            params["object_ids"] = object_ids
        
        csv_data = self.get_raw("/data/aggregate", params=params)
        return self._csv_to_dataframe(csv_data) if return_dataframe else csv_data

    def get_combined_data(
        self, 
        system_id: int, 
        start: str, 
        end: str, 
        level: str = "hour",
        object_ids: Optional[str] = None,
        return_dataframe: bool = True
    ) -> Union[str, pd.DataFrame]:
        """Get combined data."""
        params = {
            "system_id": system_id,
            "start": start,
            "end": end,
            "agg": level
        }
        if object_ids:
            params["object_ids"] = object_ids
        
        csv_data = self.get_raw("/data/combined", params=params)
        return self._csv_to_dataframe(csv_data) if return_dataframe else csv_data

    # Alert API methods
    def get_alerts(
        self, 
        system_id: int, 
        start_added: Optional[str] = None, 
        end_added: Optional[str] = None, 
        page: Optional[int] = None, 
        limit: Optional[int] = None, 
        language: str = "EN"
    ) -> Dict[str, Any]:
        """Get system alerts."""
        params = {"system_id": system_id, "language": language}
        
        if start_added:
            params["start_added"] = start_added
        if end_added:
            params["end_added"] = end_added
        if page:
            params["page"] = page
        if limit:
            params["limit"] = limit
            
        return self.get("/alerts/system", params=params)

    def get_alert_types(self, language: str = "EN") -> Dict[str, Any]:
        """Get available alert types."""
        return self.get("/alerts/types", params={"language": language})

    # Utility methods
    def _csv_to_dataframe(self, csv_data: str) -> pd.DataFrame:
        """Convert CSV string to pandas DataFrame."""
        if not csv_data or not csv_data.strip():
            return pd.DataFrame()
            
        try:
            df = pd.read_csv(StringIO(csv_data))
            
            # Parse datetime columns
            for col in ['Datetime', 'DATETIME']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
                    df.set_index(col, inplace=True)
                    break
                    
            # Convert numeric columns
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except (ValueError, TypeError):
                    pass
                    
            return df
        except Exception as e:
            self.logger.warning(f"Failed to parse CSV data: {e}")
            return pd.DataFrame()

    def _get_safe_date_range(self, days_back: int, level: str = "day") -> tuple[str, str]:
        """Get safe date range that respects API limits."""
        end = datetime.now()
        
        if level == "minute":
            requested_minutes = days_back * 24 * 60
            if requested_minutes > self.SAFE_LIMIT_MINUTES:
                actual_minutes = self.SAFE_LIMIT_MINUTES
                self.logger.warning(f"Limiting request to {actual_minutes / (24 * 60):.2f} days for minute-level data")
            else:
                actual_minutes = requested_minutes
            start = end - timedelta(minutes=actual_minutes)
        else:
            if days_back > self.MAX_DAYS_REQUEST:
                days_back = self.MAX_DAYS_REQUEST
                self.logger.warning(f"Limiting request to {days_back} days")
            start = end - timedelta(days=days_back, minutes=5)  # Small buffer
        
        return start.isoformat(), end.isoformat()

    # High-level analysis methods
    def get_date_range_data(
        self, 
        system_id: int, 
        days_back: int = 7, 
        level: str = "hour"
    ) -> pd.DataFrame:
        """Get data for a specific date range with safe limits."""
        try:
            start, end = self._get_safe_date_range(days_back, level)
            return self.get_combined_data(system_id, start, end, level=level)
        except Exception as e:
            self.logger.warning(f"Could not get date range data: {e}")
            return pd.DataFrame()

    def calculate_system_efficiency(
        self, 
        system_id: int, 
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Calculate comprehensive system efficiency metrics."""
        try:
            # Get rated power from multiple sources
            rated_power_dc = 0
            
            # Try system list first
            systems = self.list_systems()
            for sys in systems.get("systems", []):
                if sys.get("system_id") == system_id:
                    rated_power_dc = sys.get("power_rating", 0)
                    break
            
            # Fallback to system details
            if rated_power_dc == 0:
                system_details = self.get_system(system_id)
                rated_power_dc = system_details.get("system", {}).get("power_rating", 0)
            
            if rated_power_dc == 0:
                return {"error": "Could not determine system rated power"}
            
            # Get historical data
            df = self.get_date_range_data(system_id, days_back, level="hour")
            
            if df.empty:
                return {"error": "No data available for efficiency calculation"}
            
            # Filter to daylight hours only
            if hasattr(df.index, 'hour'):
                daylight_mask = (df.index.hour >= self.DAYLIGHT_START_HOUR) & (df.index.hour <= self.DAYLIGHT_END_HOUR)
                daylight_df = df[daylight_mask]
                power_values = daylight_df.iloc[:, 0].dropna()
                productive_hours = power_values[power_values > (rated_power_dc * self.MIN_PRODUCTION_THRESHOLD)]
            else:
                power_values = df.iloc[:, 0].dropna()
                productive_hours = power_values[power_values > (rated_power_dc * self.MIN_PRODUCTION_THRESHOLD)]
            
            if len(productive_hours) == 0:
                return {"error": "No valid productive daylight hours found"}
            
            # Calculate metrics
            peak_power = productive_hours.max()
            average_power_daylight = productive_hours.mean()
            average_efficiency = (average_power_daylight / rated_power_dc) * 100
            
            return {
                "rated_power_dc": rated_power_dc,
                "peak_power": peak_power,
                "average_power_daylight": average_power_daylight,
                "average_efficiency_percent": average_efficiency,
                "analysis_period_days": days_back,
                "total_data_points": len(df),
                "productive_data_points": len(productive_hours),
                "capacity_factor": (average_power_daylight / rated_power_dc) * 100,
                "peak_efficiency": (peak_power / rated_power_dc) * 100
            }
            
        except Exception as e:
            return {"error": f"Efficiency calculation failed: {e}"}

    def get_system_info(self, system_id: int) -> Dict[str, Any]:
        """Get consolidated system information."""
        try:
            return {
                "system": self.get_system(system_id),
                "layout": self.get_system_layout(system_id),
                "sources": self.get_sources(system_id),
                "summary": self.get_summary(system_id)
            }
        except Exception as e:
            return {"error": f"Failed to get system info: {e}"}
