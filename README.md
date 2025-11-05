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

## Related Projects

- [sessh](https://github.com/CommandAGI/sessh) - Core CLI
- [sessh-mcp](https://github.com/CommandAGI/sessh-mcp) - MCP server for Cursor
- [sessh-typescript-sdk](https://github.com/CommandAGI/sessh-typescript-sdk) - TypeScript SDK

## License

MIT License - see LICENSE file for details.

