#!/usr/bin/env python3
"""
Test script for TigoClient

"""

import os

# Load .env file if it exists
from dotenv import load_dotenv
load_dotenv()
print("✓ Loaded .env file")


from tigo_python.client import TigoClient

def main():
    print("Testing TigoClient...")
    
    # Test basic import
    print("✓ Import successful")
    
    # Test with environment variables
    username = os.getenv("TIGO_USERNAME")
    password = os.getenv("TIGO_PASSWORD")
    
    if username and password:
        try:
            print("Testing with credentials from environment...")
            with TigoClient(username, password) as client:
                systems = client.list_systems()
                print(f"✓ Found {len(systems.get('systems', []))} systems")
                
                if systems.get('systems'):
                    system_id = systems['systems'][0]['system_id']
                    print(f"✓ Testing with system {system_id}")
                    
                    # Test basic functionality
                    summary = client.get_summary(system_id)
                    print(f"✓ Got system summary: {summary.get('summary', {}).get('name', 'Unknown')}")
                    
        except Exception as e:
            print(f"✗ Error testing with credentials: {e}")
    else:
        print("No credentials found in environment variables")
        print("Set TIGO_USERNAME and TIGO_PASSWORD to test with real data")

if __name__ == "__main__":
    main()