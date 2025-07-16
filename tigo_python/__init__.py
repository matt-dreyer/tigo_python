# tigo_python/__init__.py
"""
Modern Python library for interacting with the Tigo Energy API.

This library provides clean, efficient access to Tigo Energy's monitoring API,
allowing users to retrieve system information, performance data, and analytics
for their solar installations.
"""

from .client import TigoClient
from .auth import TigoAuthenticator
from .exceptions import (
    TigoAPIError, 
    TigoAuthenticationError, 
    TigoRateLimitError,
    TigoConnectionError
)

__version__ = "0.2.0"
__author__ = "Matt Dreyer"
__email__ = "matt_dreyer@hotmail.com"

__all__ = [
    "TigoClient",
    "TigoAuthenticator",
    "TigoAPIError", 
    "TigoAuthenticationError",
    "TigoRateLimitError",
    "TigoConnectionError",
]