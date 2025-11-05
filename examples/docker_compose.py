#!/usr/bin/env python3
"""Example: Using sessh with Docker Compose."""
import subprocess
import os
import sys
import tempfile
from sessh import SesshClient

def main():
    """Run Docker Compose example."""
    compose_file = os.environ.get("COMPOSE_FILE", "docker-compose.yml")
    service_name = os.environ.get("SERVICE_NAME", "test-service")
    alias = "compose-test"
    ssh_port = os.environ.get("SSH_PORT", "2222")
    
    print(f"=== Docker Compose Sessh Example ===")
    print(f"Service: {service_name}")
    print()
    
    # Check if Docker Compose is available
    try:
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: docker-compose is required but not installed.", file=sys.stderr)
        sys.exit(1)
    
    # Generate SSH key if needed
    ssh_key_path = os.path.expanduser("~/.ssh/id_ed25519")
    if not os.path.exists(ssh_key_path):
        print("Generating SSH key...")
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", ssh_key_path, "-N", "", "-q"],
            check=True
        )
    
    # Read public key
    with open(f"{ssh_key_path}.pub") as f:
        ssh_pubkey = f.read().strip()
    
    # Create docker-compose.yml
    compose_content = f"""version: '3.8'
services:
  {service_name}:
    image: ubuntu:22.04
    ports:
      - "{ssh_port}:22"
    environment:
      - SSH_PUBKEY={ssh_pubkey}
    command: >
      bash -c "
        apt-get update -qq &&
        apt-get install -y -qq openssh-server tmux sudo &&
        mkdir -p /var/run/sshd &&
        echo 'root:testpass' | chpasswd &&
        sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config &&
        mkdir -p /root/.ssh &&
        echo \"${{SSH_PUBKEY}}\" > /root/.ssh/authorized_keys &&
        chmod 700 /root/.ssh &&
        chmod 600 /root/.ssh/authorized_keys &&
        /usr/sbin/sshd -D
      "
"""
    
    cleanup_file = False
    if not os.path.exists(compose_file):
        cleanup_file = True
    
    try:
        with open(compose_file, "w") as f:
            f.write(compose_content)
        
        # Start services
        print("Starting Docker Compose services...")
        subprocess.run(["docker-compose", "-f", compose_file, "up", "-d"], check=True)
        
        # Wait for SSH to be ready
        print("Waiting for SSH server to be ready...")
        for _ in range(30):
            result = subprocess.run([
                "ssh", "-o", "ConnectTimeout=2", "-o", "StrictHostKeyChecking=no",
                "-p", ssh_port, "root@localhost", "echo", "ready"
            ], capture_output=True, timeout=5)
            if result.returncode == 0:
                break
        
        # Get container info
        result = subprocess.run([
            "docker-compose", "-f", compose_file, "ps", "-q", service_name
        ], capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()
        print(f"Container ID: {container_id}")
        
        # Create client
        client = SesshClient(
            alias=alias,
            host="root@localhost",
            port=int(ssh_port),
            identity=ssh_key_path
        )
        
        try:
            # Open session
            print("Opening sessh session...")
            client.open()
            
            # Run commands
            print("Running commands...")
            client.run("echo 'Hello from Docker Compose service!'")
            client.run("hostname")
            client.run("apt-get update -qq")
            client.run("which tmux")
            client.run("cd /tmp && pwd && echo 'State persisted across commands!'")
            
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
            
            # Show Docker Compose status
            print()
            print("=== Docker Compose Status ===")
            subprocess.run(["docker-compose", "-f", compose_file, "ps"])
            
            print()
            print("Example completed successfully!")
            
        finally:
            client.close()
            
    finally:
        # Cleanup
        print("Cleaning up...")
        subprocess.run(["docker-compose", "-f", compose_file, "down"], capture_output=True)
        if cleanup_file and os.path.exists(compose_file):
            os.remove(compose_file)

if __name__ == "__main__":
    main()

