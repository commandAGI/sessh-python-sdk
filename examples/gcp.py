#!/usr/bin/env python3
"""Example: Using sessh with Google Cloud Platform Compute Engine."""
import subprocess
import time
import os
import sys
from sessh import SesshClient

def main():
    """Run GCP example."""
    project = os.environ.get("GCP_PROJECT", "")
    zone = os.environ.get("GCP_ZONE", "us-central1-a")
    instance_type = os.environ.get("GCP_INSTANCE_TYPE", "n1-standard-1")
    image_project = os.environ.get("GCP_IMAGE_PROJECT", "ubuntu-os-cloud")
    image_family = os.environ.get("GCP_IMAGE_FAMILY", "ubuntu-2204-lts")
    instance_name = f"sessh-example-{int(time.time())}"
    alias = "gcp-agent"
    
    print(f"=== GCP Compute Engine Sessh Example ===")
    print(f"Zone: {zone}")
    print(f"Instance Type: {instance_type}")
    print()
    
    # Check prerequisites
    try:
        subprocess.run(["gcloud", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: gcloud CLI is required but not installed.", file=sys.stderr)
        sys.exit(1)
    
    # Get default project if not set
    if not project:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            project = result.stdout.strip()
    
    if not project:
        print("Error: GCP_PROJECT must be set or gcloud must be configured.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Project: {project}")
    
    ip = None
    
    try:
        # Launch instance
        print("Creating GCP instance...")
        subprocess.run([
            "gcloud", "compute", "instances", "create", instance_name,
            "--zone", zone,
            "--machine-type", instance_type,
            "--image-project", image_project,
            "--image-family", image_family,
            "--project", project,
            "--metadata", "enable-oslogin=FALSE",
            "--tags", "sessh-example"
        ], check=True)
        
        # Get IP address
        print("Getting instance IP address...")
        for _ in range(30):
            result = subprocess.run([
                "gcloud", "compute", "instances", "describe", instance_name,
                "--zone", zone,
                "--project", project,
                "--format", "get(networkInterfaces[0].accessConfigs[0].natIP)"
            ], capture_output=True, text=True, check=True)
            
            ip = result.stdout.strip()
            if ip and ip != "None":
                break
            time.sleep(2)
        
        if not ip or ip == "None":
            print("Error: Failed to get instance IP address.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Instance IP: {ip}")
        
        # Wait for SSH to be ready
        print("Waiting for SSH to be ready...")
        for _ in range(60):
            result = subprocess.run([
                "ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
                f"ubuntu@{ip}", "echo", "ready"
            ], capture_output=True, timeout=10)
            if result.returncode == 0:
                break
            time.sleep(5)
        
        # Create client
        client = SesshClient(alias=alias, host=f"ubuntu@{ip}")
        
        try:
            # Open session
            print("Opening sessh session...")
            client.open()
            
            # Install dependencies and run workload
            print("Installing dependencies...")
            client.run("sudo apt-get update -qq")
            client.run("sudo apt-get install -y -qq python3-pip tmux")
            
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
            print(f"Instance {instance_name} will be deleted on exit.")
            
        finally:
            client.close()
            
    finally:
        # Cleanup
        if instance_name:
            print("Cleaning up...")
            subprocess.run([
                "gcloud", "compute", "instances", "delete", instance_name,
                "--zone", zone,
                "--project", project,
                "--quiet"
            ], capture_output=True)

if __name__ == "__main__":
    main()

