#!/usr/bin/env python3
"""Example: Using sessh with Lambda Labs GPU instances."""
import json
import subprocess
import time
import os
import sys
import urllib.request
import urllib.error
from sessh import SesshClient

def main():
    """Run Lambda Labs example."""
    api_key = os.environ.get("LAMBDA_API_KEY", "")
    region = os.environ.get("LAMBDA_REGION", "us-west-1")
    instance_type = os.environ.get("LAMBDA_INSTANCE_TYPE", "gpu_1x_a10")
    ssh_key = os.environ.get("LAMBDA_SSH_KEY", "")
    alias = "lambda-agent"
    
    print(f"=== Lambda Labs GPU Sessh Example ===")
    print(f"Region: {region}")
    print(f"Instance Type: {instance_type}")
    print()
    
    if not api_key:
        print("Error: LAMBDA_API_KEY environment variable must be set with your Lambda Labs API key.", file=sys.stderr)
        sys.exit(1)
    
    if not ssh_key:
        print("Error: LAMBDA_SSH_KEY environment variable must be set with your Lambda Labs SSH key name.", file=sys.stderr)
        sys.exit(1)
    
    instance_id = None
    ip = None
    
    def make_request(method, url, data=None):
        """Make authenticated request to Lambda Labs API."""
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Basic {api_key}:")
        if data:
            req.add_header("Content-Type", "application/json")
            req.data = json.dumps(data).encode()
        req.get_method = lambda: method
        return urllib.request.urlopen(req)
    
    try:
        # Launch instance
        print("Launching Lambda Labs instance...")
        response = make_request(
            "POST",
            "https://cloud.lambdalabs.com/api/v1/instance-operations/launch",
            {
                "region_name": region,
                "instance_type_name": instance_type,
                "ssh_key_names": [ssh_key],
                "quantity": 1
            }
        )
        launch_data = json.loads(response.read())
        
        if "instance_ids" not in launch_data.get("data", {}):
            print(f"Error: Failed to launch instance. Response: {launch_data}", file=sys.stderr)
            sys.exit(1)
        
        instance_id = launch_data["data"]["instance_ids"][0]
        print(f"Instance ID: {instance_id}")
        
        # Wait for IP
        print("Waiting for instance IP address...")
        for _ in range(60):
            response = make_request("GET", "https://cloud.lambdalabs.com/api/v1/instances")
            instances_data = json.loads(response.read())
            
            for inst in instances_data.get("data", []):
                if inst["id"] == instance_id:
                    ip = inst.get("ip")
                    if ip and ip != "null":
                        break
            
            if ip and ip != "null":
                break
            time.sleep(5)
        
        if not ip or ip == "null":
            print("Error: Failed to get instance IP address.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Instance IP: {ip}")
        
        # Wait for SSH to be ready
        print("Waiting for SSH to be ready...")
        for _ in range(60):
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
                 f"ubuntu@{ip}", "echo", "ready"],
                capture_output=True,
                timeout=10
            )
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
            client.run("pip install torch torchvision")
            client.run("python3 -c 'import torch; print(f\"PyTorch version: {torch.__version__}\")'")
            
            print("Running workload...")
            client.run("cd /tmp && pwd && echo 'Working directory: $(pwd)' && echo 'State persisted across commands!'")
            client.run("nvidia-smi || echo 'GPU check (may not be available in all instance types)'")
            
            # Get logs
            print()
            print("=== Session Logs ===")
            logs = client.logs(200)
            print(logs.get("output", ""))
            
            # Check status
            print()
            print("=== Session Status ===")
            status = client.status()
            print(f"Master: {status.get('master')}, Session: {status.get('session')}")
            
            print()
            print("Example completed successfully!")
            print(f"Instance {instance_id} will be terminated on exit.")
            
        finally:
            client.close()
            
    finally:
        # Cleanup
        if instance_id:
            print("Cleaning up...")
            try:
                make_request(
                    "POST",
                    "https://cloud.lambdalabs.com/api/v1/instance-operations/terminate",
                    {"instance_ids": [instance_id]}
                )
            except Exception:
                pass

if __name__ == "__main__":
    main()

