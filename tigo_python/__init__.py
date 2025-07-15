# tigo_python/__init__.py
"""
A modern Python library for interacting with the Tigo Energy API.

This library provides easy access to Tigo Energy's monitoring API,
allowing users to retrieve system information, performance data,
and analytics for their solar installations.
"""

from .client import TigoClient
from .auth import TigoAuthenticator
from .exceptions import TigoAPIError, TigoAuthenticationError
import importlib.metadata


__version__ = "0.1.0"
__author__ = "Matt Dreyer"
__email__ = "matt_dreyer@hotmail.com"

__all__ = [
    "TigoClient",
    "TigoAPIError", 
    "TigoAuthenticationError",
]