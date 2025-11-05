# Sessh Python SDK

Python SDK for [sessh](https://github.com/CommandAGI/sessh) - a pure stdlib implementation with no external dependencies.

## Installation

```bash
pip install -e .
```

Or from source:

```bash
git clone https://github.com/CommandAGI/sessh-python-sdk.git
cd sessh-python-sdk
pip install -e .
```

## Prerequisites

- Python 3.8+
- The `sessh` CLI must be installed and on your PATH

## Usage

```python
from sessh import SesshClient

# Create a client
client = SesshClient(
    alias="agent",
    host="ubuntu@203.0.113.10",
    identity="~/.ssh/id_ed25519"
)

# Open a session
client.open()

# Run commands
client.run("python train.py")

# Get logs
logs = client.logs(400)
print(logs["output"])

# Check status
status = client.status()
print(f"Master: {status['master']}, Session: {status['session']}")

# Close session
client.close()
```

## API Reference

### `SesshClient(alias, host, port=None, sessh_bin=None, identity=None, proxyjump=None)`

Initialize a sessh client.

**Parameters:**
- `alias` (str): Session alias name
- `host` (str): SSH host (user@host)
- `port` (int, optional): SSH port (default: 22)
- `sessh_bin` (str, optional): Path to sessh binary (default: "sessh" from PATH)
- `identity` (str, optional): Path to SSH private key
- `proxyjump` (str, optional): ProxyJump host (e.g., "bastionuser@bastion")

### Methods

#### `open() -> Dict[str, Any]`
Open or ensure a persistent remote tmux session.

#### `run(command: str) -> Dict[str, Any]`
Send a command into the persistent tmux session.

#### `logs(lines: int = 300) -> Dict[str, Any]`
Capture recent output from the tmux session.

#### `status() -> Dict[str, Any]`
Check whether the SSH controlmaster and tmux session exist.

#### `close() -> Dict[str, Any]`
Kill tmux session and close the controlmaster.

#### `attach() -> None`
Attach to the tmux session interactively. Note: This will block and take over the terminal.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Examples

Comprehensive examples are available in the [`examples/`](examples/) directory. Each example demonstrates launching infrastructure, using sessh to manage persistent sessions, and cleaning up resources.

### Quick Examples

#### Local/Localhost

```python
from sessh import SesshClient

client = SesshClient(alias="local-test", host="user@localhost")
client.open()
client.run("echo 'Hello from sessh!'")
logs = client.logs(50)
print(logs["output"])
client.close()
```

#### AWS EC2

```python
import os
from sessh import SesshClient

# Launch EC2 instance, get IP (example)
ip = "203.0.113.10"
client = SesshClient(alias="aws-agent", host=f"ubuntu@{ip}")
client.open()
client.run("python train.py")
logs = client.logs(400)
client.close()
```

#### Lambda Labs GPU

```python
import os
from sessh import SesshClient

# Launch Lambda Labs instance, get IP (example)
ip = "203.0.113.10"
client = SesshClient(
    alias="lambda-agent",
    host=f"ubuntu@{ip}",
    identity="~/.ssh/id_ed25519"
)
client.open()
client.run("pip install torch torchvision")
client.run("python train.py")
logs = client.logs(400)
print(logs["output"])
client.close()
```

### Available Examples

All examples follow the same pattern:
1. Launch infrastructure (instance/container)
2. Wait for SSH to be ready
3. Open sessh session
4. Run commands (state persists between commands)
5. Fetch logs
6. Clean up resources

**Example Files:**
- [`examples/local.py`](examples/local.py) - Localhost/local VM
- [`examples/docker.py`](examples/docker.py) - Docker container
- [`examples/aws.py`](examples/aws.py) - AWS EC2
- [`examples/gcp.py`](examples/gcp.py) - Google Cloud Platform
- [`examples/lambdalabs.py`](examples/lambdalabs.py) - Lambda Labs GPU
- [`examples/azure.py`](examples/azure.py) - Microsoft Azure
- [`examples/digitalocean.py`](examples/digitalocean.py) - DigitalOcean
- [`examples/docker_compose.py`](examples/docker_compose.py) - Docker Compose

**Running Examples:**
```bash
# Local example
python examples/local.py localhost

# AWS example (requires AWS credentials)
export AWS_REGION=us-east-1
export AWS_KEY_NAME=my-key
python examples/aws.py

# Lambda Labs example (requires API key)
export LAMBDA_API_KEY=sk_live_...
export LAMBDA_SSH_KEY=my-ssh-key
python examples/lambdalabs.py
```

### Integration Tests

Integration tests are available in [`tests/test_examples.py`](tests/test_examples.py). These tests require real infrastructure and are skipped by default.

**Running Integration Tests:**
```bash
# Enable integration tests
export SESSH_INTEGRATION_TESTS=1

# For local tests
export SESSH_TEST_HOST=localhost
pytest tests/test_examples.py::TestLocalExample

# For cloud provider tests (requires credentials)
export AWS_REGION=us-east-1
pytest tests/test_examples.py::TestAWSExample
```

### Error Handling

```python
from sessh import SesshClient
import sys

client = SesshClient(alias="test", host="ubuntu@host")

try:
    client.open()
    client.run("some-command")
except RuntimeError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    client.close()
```

## Troubleshooting

**"sessh: command not found"**
- Ensure `sessh` CLI is installed and on PATH
- Or set `sessh_bin` parameter: `SesshClient(..., sessh_bin="/usr/local/bin/sessh")`

**RuntimeError on operations**
- Check that `sessh` CLI works from command line
- Verify SSH key permissions and configuration
- Ensure remote host has tmux installed

**JSON parsing errors**
- The SDK automatically sets `SESSH_JSON=1`
- Verify `sessh` CLI supports JSON output

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Related Projects

- [sessh](https://github.com/CommandAGI/sessh) - Core CLI
- [sessh-mcp](https://github.com/CommandAGI/sessh-mcp) - MCP server for Cursor
- [sessh-typescript-sdk](https://github.com/CommandAGI/sessh-typescript-sdk) - TypeScript SDK

## License

MIT License - see LICENSE file for details.

