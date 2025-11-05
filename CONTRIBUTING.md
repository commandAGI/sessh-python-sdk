# Contributing to Sessh Python SDK

Thank you for contributing to sessh-python-sdk, a pure stdlib Python client for managing persistent SSH sessions.

## Philosophy

The Python SDK is intentionally minimal:

1. **Pure stdlib**: No external dependencies. We use `subprocess` and `json` only.
2. **Thin Wrapper**: We call `sessh` CLI and parse JSON. No SSH logic here.
3. **Fail Loudly**: If `sessh` fails, we raise exceptions. No silent failures.
4. **Type Hints**: We use type hints for better developer experience.

## Development Setup

### Prerequisites

- Python 3.8+
- The `sessh` CLI must be installed and on PATH
- `pytest` (for development, optional)

### Setup

```bash
# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

Note: Tests require a test SSH host. See `tests/test_client.py` for test configuration.

## Code Style

- Use type hints everywhere
- Follow PEP 8
- Use `subprocess.run()` for CLI calls
- Always set `SESSH_JSON=1` in environment
- Raise `RuntimeError` with clear messages on failure
- Use docstrings for all public methods

## Architecture

The SDK is a simple wrapper:

1. **Client initialization**: Store alias, host, port, and options
2. **Command execution**: Build `sessh` CLI args, set environment, call subprocess
3. **Response parsing**: Parse JSON output, return as dict
4. **Error handling**: Raise exceptions on failure

Key design decisions:

- Pure stdlib (no `requests`, `click`, etc.)
- JSON mode forced for all calls
- Exceptions raised on failure (no return codes)
- Type hints for better IDE support

## Adding Features

If `sessh` CLI adds new commands, add corresponding SDK methods:

1. Add method to `SesshClient` class:
   ```python
   def new_method(self, param: str) -> Dict[str, Any]:
       """
       Description of what it does.
       
       Args:
           param: Description of param
           
       Returns:
           Dict with sessh response
           
       Raises:
           RuntimeError: If sessh command fails
       """
       return self._run_sessh("newcommand", param)
   ```

2. Update README.md with new method documentation

3. Add tests to `tests/test_client.py`

4. Update type hints if return structure changes

## Submitting Changes

1. **Fork the repository** (if needed)

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Keep stdlib-only (no new dependencies)
   - Add type hints
   - Add docstrings
   - Write tests

4. **Run tests**:
   ```bash
   pytest
   ```

5. **Commit and push**:
   ```bash
   git commit -m "feat: add support for X"
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- **Describe the change**: What does it do? Why is it needed?
- **Show it works**: Include code examples
- **Keep it focused**: One feature or fix per PR
- **Update docs**: README.md should reflect new functionality
- **Add tests**: New features should have tests

## What We're Looking For

### High Priority

- **Error handling**: Better error messages, exception types
- **Type hints**: More specific types, better annotations
- **Documentation**: More examples, usage patterns
- **Testing**: Better test coverage

### Nice to Have

- **Performance**: Faster subprocess execution (if possible with stdlib)
- **Features**: New methods if `sessh` CLI adds commands
- **Developer experience**: Better error messages, debugging helpers

### Not Looking For

- **External dependencies**: We want to stay stdlib-only
- **Async support**: If you need async, use `asyncio.subprocess` yourself
- **SSH logic**: That's in `sessh` CLI, not here

## Questions?

Open an issue with the `question` label. We're happy to help!

