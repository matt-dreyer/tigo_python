# config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class TigoConfig:
    base_url: str = "https://api2.tigoenergy.com/api/v3"
    timeout: float = 30.0
    safe_limit_minutes: int = 20150
    default_page_size: int = 50
    
    @classmethod
    def from_env(cls) -> 'TigoConfig':
        # Load from environment variables
        pass