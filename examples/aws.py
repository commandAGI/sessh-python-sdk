#!/usr/bin/env python3
"""Example: Using sessh with AWS EC2."""
import subprocess
import json
import time
import os
import sys
from sessh import SesshClient

def main():
    """Run AWS example."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    instance_type = os.environ.get("INSTANCE_TYPE", "t2.micro")
    key_name = os.environ.get("AWS_KEY_NAME", "")
    security_group = os.environ.get("AWS_SECURITY_GROUP", "")
    alias = "aws-agent"
    
    print(f"=== AWS EC2 Sessh Example ===")
    print(f"Region: {region}")
    print(f"Instance Type: {instance_type}")
    print()
    
    # Check prerequisites
    try:
        subprocess.run(["aws", "--version"], check=True, capture_output=True)
        subprocess.run(["jq", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error: Required tool not found: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get default values if not set
    if not key_name:
        result = subprocess.run(
            ["aws", "ec2", "describe-key-pairs", "--query", "KeyPairs[0].KeyName", "--output", "text"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            key_name = result.stdout.strip()
    
    if not key_name:
        print("Error: AWS_KEY_NAME must be set or at least one key pair must exist.", file=sys.stderr)
        sys.exit(1)
    
    # Get Ubuntu AMI
    if not os.environ.get("AWS_AMI_ID"):
        result = subprocess.run([
            "aws", "ec2", "describe-images",
            "--owners", "099720109477",
            "--filters", "Name=name,Values=ubuntu/images/h2-ssd/ubuntu-jammy-22.04-amd64-server-*",
                         "Name=state,Values=available",
            "--query", "Images | sort_by(@, &CreationDate) | [-1].ImageId",
            "--output", "text",
            "--region", region
        ], capture_output=True, text=True, check=True)
        ami_id = result.stdout.strip()
    else:
        ami_id = os.environ.get("AWS_AMI_ID")
    
    if not security_group:
        result = subprocess.run([
            "aws", "ec2", "describe-security-groups",
            "--filters", "Name=ip-permission.from-port,Values=22",
                         "Name=ip-permission.to-port,Values=22",
                         "Name=ip-permission.protocol,Values=tcp",
            "--query", "SecurityGroups[0].GroupId",
            "--output", "text",
            "--region", region
        ], capture_output=True, text=True)
        if result.returncode == 0:
            security_group = result.stdout.strip()
    
    if not security_group:
        print("Error: AWS_SECURITY_GROUP must be set or a security group allowing SSH must exist.", file=sys.stderr)
        sys.exit(1)
    
    instance_id = None
    ip = None
    
    try:
        # Launch instance
        print("Launching EC2 instance...")
        result = subprocess.run([
            "aws", "ec2", "run-instances",
            "--image-id", ami_id,
            "--instance-type", instance_type,
            "--key-name", key_name,
            "--security-group-ids", security_group,
            "--tag-specifications", f"ResourceType=instance,Tags=[{{Key=Name,Value=sessh-example}}]",
            "--region", region,
            "--output", "json"
        ], capture_output=True, text=True, check=True)
        
        launch_data = json.loads(result.stdout)
        instance_id = launch_data["Instances"][0]["InstanceId"]
        print(f"Instance ID: {instance_id}")
        
        # Wait for instance to be running
        print("Waiting for instance to be running...")
        subprocess.run([
            "aws", "ec2", "wait", "instance-running",
            "--instance-ids", instance_id,
            "--region", region
        ], check=True)
        
        # Get IP address
        print("Getting instance IP address...")
        for _ in range(30):
            result = subprocess.run([
                "aws", "ec2", "describe-instances",
                "--instance-ids", instance_id,
                "--query", "Reservations[0].Instances[0].PublicIpAddress",
                "--output", "text",
                "--region", region
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
            print(f"Instance {instance_id} will be terminated on exit.")
            
        finally:
            client.close()
            
    finally:
        # Cleanup
        if instance_id:
            print("Cleaning up...")
            subprocess.run([
                "aws", "ec2", "terminate-instances",
                "--instance-ids", instance_id,
                "--region", region
            ], capture_output=True)

if __name__ == "__main__":
    main()

