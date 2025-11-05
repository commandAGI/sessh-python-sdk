#!/usr/bin/env python3
"""Example: Using sessh with a localhost or local VM."""
import sys
import os
from sessh import SesshClient

def main():
    """Run local example."""
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    user = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    alias = "local-test"
    
    print(f"=== Local Sessh Example ===")
    print(f"Host: {user}@{host}")
    print()
    
    client = SesshClient(alias=alias, host=f"{user}@{host}")
    
    try:
        # Open session
        print("Opening sessh session...")
        client.open()
        
        # Run commands
        print("Running commands...")
        client.run("echo 'Hello from sessh!'")
        client.run("pwd")
        client.run("whoami")
        client.run("cd /tmp && pwd && echo 'State persisted!'")
        
        # Get logs
        print()
        print("=== Session Logs ===")
        logs = client.logs(50)
        print(logs.get("output", ""))
        
        # Check status
        print()
        print("=== Session Status ===")
        status = client.status()
        print(f"Master: {status.get('master')}, Session: {status.get('session')}")
        
        print()
        print("Example completed successfully!")
        
    finally:
        client.close()

if __name__ == "__main__":
    main()

