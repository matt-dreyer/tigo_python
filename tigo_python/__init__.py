# tigo_python/__init__.py
"""
Tigo Energy API Python Wrapper
"""

from .client import TigoClient
from .auth import TigoAuthenticator
from .exceptions import TigoAPIError
import importlib.metadata

__version__ = importlib.metadata.version("tigo_python")
__all__ = ["TigoClient", "TigoAuthenticator", "TigoAPIError"]
