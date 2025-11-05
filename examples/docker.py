#!/usr/bin/env python3
"""Example: Using sessh with a Docker container."""
import subprocess
import time
import os
import sys
from sessh import SesshClient

def main():
    """Run Docker example."""
    container_name = f"sessh-test-{int(time.time())}"
    image = "ubuntu:22.04"
    alias = "docker-test"
    ssh_port = os.environ.get("SSH_PORT", "2222")
    
    print(f"=== Docker Sessh Example ===")
    print(f"Container: {container_name}")
    print()
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: docker is required but not installed.", file=sys.stderr)
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
    
    try:
        # Start Docker container with SSH server
        print("Starting Docker container with SSH server...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{ssh_port}:22",
            "-e", f"SSH_PUBKEY={ssh_pubkey}",
            image,
            "bash", "-c", """
                apt-get update -qq && \
                apt-get install -y -qq openssh-server tmux sudo && \
                mkdir -p /var/run/sshd && \
                echo 'root:testpass' | chpasswd && \
                sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
                mkdir -p /root/.ssh && \
                echo \"${SSH_PUBKEY}\" > /root/.ssh/authorized_keys && \
                chmod 700 /root/.ssh && \
                chmod 600 /root/.ssh/authorized_keys && \
                /usr/sbin/sshd -D
            """
        ], check=True)
        
        # Wait for SSH to be ready
        print("Waiting for SSH server to be ready...")
        for _ in range(30):
            try:
                result = subprocess.run(
                    ["ssh", "-o", "ConnectTimeout=2", "-o", "StrictHostKeyChecking=no",
                     "-p", ssh_port, "root@localhost", "echo", "ready"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    break
            except subprocess.TimeoutExpired:
                pass
            time.sleep(2)
        
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
            client.run("echo 'Hello from Docker container!'")
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
            
            print()
            print("Example completed successfully!")
            
        finally:
            client.close()
            
    finally:
        # Cleanup
        print("Cleaning up...")
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        subprocess.run(["docker", "rm", container_name], capture_output=True)

if __name__ == "__main__":
    main()

