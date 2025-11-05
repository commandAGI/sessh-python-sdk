#!/usr/bin/env python3
"""Example: Using sessh with DigitalOcean Droplets."""
import subprocess
import time
import os
import sys
from sessh import SesshClient

def main():
    """Run DigitalOcean example."""
    token = os.environ.get("DO_TOKEN", "")
    region = os.environ.get("DO_REGION", "nyc1")
    size = os.environ.get("DO_SIZE", "s-1vcpu-1gb")
    image = os.environ.get("DO_IMAGE", "ubuntu-22-04-x64")
    droplet_name = f"sessh-example-{int(time.time())}"
    alias = "do-agent"
    
    print(f"=== DigitalOcean Droplet Sessh Example ===")
    print(f"Region: {region}")
    print(f"Size: {size}")
    print(f"Image: {image}")
    print()
    
    # Check prerequisites
    try:
        subprocess.run(["doctl", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: doctl CLI is required but not installed.", file=sys.stderr)
        sys.exit(1)
    
    if not token:
        print("Error: DO_TOKEN environment variable must be set with your DigitalOcean API token.", file=sys.stderr)
        sys.exit(1)
    
    # Authenticate doctl
    subprocess.run(["doctl", "auth", "init", "--access-token", token], capture_output=True)
    
    # Generate SSH key if needed
    ssh_key_path = os.path.expanduser("~/.ssh/id_ed25519")
    if not os.path.exists(ssh_key_path):
        print("Generating SSH key...")
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", ssh_key_path, "-N", "", "-q"],
            check=True
        )
    
    # Get SSH key fingerprint
    result = subprocess.run(
        ["ssh-keygen", "-l", "-f", f"{ssh_key_path}.pub", "-E", "md5"],
        capture_output=True,
        text=True,
        check=True
    )
    fingerprint = result.stdout.split()[1].replace("MD5:", "")
    
    # Add SSH key to DigitalOcean if not already present
    ssh_key_name = "sessh-key"
    result = subprocess.run(
        ["doctl", "compute", "ssh-key", "list", "--format", "ID,Fingerprint", "--no-header"],
        capture_output=True,
        text=True
    )
    if fingerprint not in result.stdout:
        print("Adding SSH key to DigitalOcean...")
        subprocess.run([
            "doctl", "compute", "ssh-key", "create", ssh_key_name,
            "--public-key-file", f"{ssh_key_path}.pub"
        ], capture_output=True)
    
    droplet_id = None
    ip = None
    
    try:
        # Launch droplet
        print("Creating DigitalOcean droplet...")
        result = subprocess.run([
            "doctl", "compute", "droplet", "create", droplet_name,
            "--region", region,
            "--size", size,
            "--image", image,
            "--ssh-keys", fingerprint,
            "--format", "ID,PublicIPv4",
            "--no-header"
        ], capture_output=True, text=True, check=True)
        
        droplet_id = result.stdout.split()[0]
        
        if not droplet_id:
            print("Error: Failed to create droplet.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Droplet ID: {droplet_id}")
        
        # Wait for droplet to be active and get IP
        print("Waiting for droplet to be active...")
        for _ in range(60):
            result = subprocess.run([
                "doctl", "compute", "droplet", "get", droplet_id,
                "--format", "ID,Status,PublicIPv4",
                "--no-header"
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                parts = result.stdout.split()
                if len(parts) >= 3:
                    status = parts[1]
                    ip = parts[2]
                    if status == "active" and ip and ip != "none":
                        break
            time.sleep(5)
        
        if not ip or ip == "none":
            print("Error: Failed to get droplet IP address.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Droplet IP: {ip}")
        
        # Wait for SSH to be ready
        print("Waiting for SSH to be ready...")
        for _ in range(60):
            result = subprocess.run([
                "ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
                "-i", ssh_key_path, f"root@{ip}", "echo", "ready"
            ], capture_output=True, timeout=10)
            if result.returncode == 0:
                break
            time.sleep(5)
        
        # Create client
        client = SesshClient(
            alias=alias,
            host=f"root@{ip}",
            identity=ssh_key_path
        )
        
        try:
            # Open session
            print("Opening sessh session...")
            client.open()
            
            # Install dependencies and run workload
            print("Installing dependencies...")
            client.run("apt-get update -qq")
            client.run("apt-get install -y -qq python3-pip tmux")
            
            print("Running workload...")
            client.run("python3 -c 'import sys; print(f\"Python version: {sys.version}\")'")
            client.run("cd /tmp && pwd && echo 'Working directory: $(pwd)' && echo 'State persisted across commands!'")
            
            # Get logs
            print()
            print("=== Session Logs ===")
            logs = client.logs(100)
            print(logs.get("output", ""))
            
            # Check status
            print()
            print("=== Session Status ===")
            status = client.status()
            print(f"Master: {status.get('master')}, Session: {status.get('session')}")
            
            print()
            print("Example completed successfully!")
            print(f"Droplet {droplet_id} will be deleted on exit.")
            
        finally:
            client.close()
            
    finally:
        # Cleanup
        if droplet_id:
            print("Cleaning up...")
            subprocess.run([
                "doctl", "compute", "droplet", "delete", droplet_id,
                "--force"
            ], capture_output=True)

if __name__ == "__main__":
    main()

