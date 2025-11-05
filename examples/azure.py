#!/usr/bin/env python3
"""Example: Using sessh with Microsoft Azure Virtual Machines."""
import subprocess
import json
import time
import os
import sys
from sessh import SesshClient

def main():
    """Run Azure example."""
    resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "sessh-example-rg")
    location = os.environ.get("AZURE_LOCATION", "eastus")
    vm_size = os.environ.get("AZURE_VM_SIZE", "Standard_B1s")
    vm_name = f"sessh-example-{int(time.time())}"
    alias = "azure-agent"
    
    print(f"=== Azure VM Sessh Example ===")
    print(f"Resource Group: {resource_group}")
    print(f"Location: {location}")
    print(f"VM Size: {vm_size}")
    print()
    
    # Check prerequisites
    try:
        subprocess.run(["az", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Azure CLI is required but not installed.", file=sys.stderr)
        sys.exit(1)
    
    # Check if logged in
    try:
        subprocess.run(["az", "account", "show"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: Not logged in to Azure. Run 'az login' first.", file=sys.stderr)
        sys.exit(1)
    
    # Generate SSH key if needed
    ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")
    if not os.path.exists(ssh_key_path):
        print("Generating SSH key...")
        subprocess.run(
            ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", ssh_key_path, "-N", "", "-q"],
            check=True
        )
    
    # Read public key
    with open(f"{ssh_key_path}.pub") as f:
        ssh_pubkey = f.read().strip()
    
    cleanup_rg = False
    ip = None
    
    try:
        # Check if resource group exists, create if not
        result = subprocess.run(
            ["az", "group", "show", "--name", resource_group],
            capture_output=True
        )
        if result.returncode != 0:
            print("Creating resource group...")
            subprocess.run([
                "az", "group", "create",
                "--name", resource_group,
                "--location", location
            ], check=True, capture_output=True)
            cleanup_rg = True
        
        # Launch VM
        print("Creating Azure VM...")
        result = subprocess.run([
            "az", "vm", "create",
            "--resource-group", resource_group,
            "--name", vm_name,
            "--image", "Ubuntu2204",
            "--size", vm_size,
            "--admin-username", "azureuser",
            "--ssh-key-values", ssh_pubkey,
            "--public-ip-sku", "Standard",
            "--output", "json"
        ], capture_output=True, text=True, check=True)
        
        vm_data = json.loads(result.stdout)
        ip = vm_data["publicIpAddress"]
        
        if not ip:
            print("Error: Failed to get VM IP address.", file=sys.stderr)
            sys.exit(1)
        
        print(f"VM IP: {ip}")
        
        # Wait for SSH to be ready
        print("Waiting for SSH to be ready...")
        for _ in range(60):
            result = subprocess.run([
                "ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
                "-i", ssh_key_path, f"azureuser@{ip}", "echo", "ready"
            ], capture_output=True, timeout=10)
            if result.returncode == 0:
                break
            time.sleep(5)
        
        # Create client
        client = SesshClient(
            alias=alias,
            host=f"azureuser@{ip}",
            identity=ssh_key_path
        )
        
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
            print(f"VM {vm_name} will be deleted on exit.")
            
        finally:
            client.close()
            
    finally:
        # Cleanup
        print("Cleaning up...")
        if vm_name:
            subprocess.run([
                "az", "vm", "delete",
                "--resource-group", resource_group,
                "--name", vm_name,
                "--yes"
            ], capture_output=True)
        
        if cleanup_rg:
            subprocess.run([
                "az", "group", "delete",
                "--name", resource_group,
                "--yes",
                "--no-wait"
            ], capture_output=True)

if __name__ == "__main__":
    main()

